# Prompt — App de demonstração do Verificador de Contestação (Fase 2: interface visual)

## Seu papel e objetivo

Você vai construir um **app web de demonstração** por cima de um verificador de contestações previdenciárias **que já existe e está pronto** (Fase 1, uma CLI em Python). O app deixa o estagiário subir uma minuta (PDF/HTML), roda o verificador existente e mostra um **diagnóstico visual** (APROVADO/REPROVADO + itens por bloco) — com o diferencial de exibir o **PDF da minuta com os erros grifados no lugar exato onde ocorrem**.

Princípio número 1: **você invoca o verificador que já existe, não reimplementa as regras.** Toda a lógica de veredito continua sendo do verificador. Você só adiciona: (a) uma camada web que o chama, (b) uma camada que localiza a evidência de cada erro dentro do PDF, e (c) a interface.

---

## Autonomia e transparência

Você tem **autonomia total** para escrever, criar e modificar o código necessário para entregar isto — arquivos novos, módulos novos, dependências, estrutura de pastas, o que julgar melhor. As assinaturas, nomes de módulos, estratégias e o contrato de dados descritos abaixo são **sugestões de referência**: se você tiver um caminho tecnicamente melhor, siga por ele. Não peça permissão para escrever código — escreva.

A única exigência em troca da autonomia é **transparência**: sempre que criar ou modificar algum arquivo/trecho de código, **explique a mudança** (o que fez e por quê) e **mostre o código** correspondente. Nada de alterações silenciosas. Se você divergir de alguma sugestão deste prompt, diga que divergiu e por quê.

A única linha que você **não** pode cruzar sem me consultar antes é mexer na lógica de regras ou no cálculo de veredito do verificador existente (ver Princípio número 1). Qualquer outra coisa: crie à vontade, só me mostre.

---

## O que já existe (reaproveitar, NÃO reescrever)

Há um pacote `verificador-contestacao/` com:

- CLI em Python: extração (`pdfplumber` p/ PDF, `BeautifulSoup` p/ HTML) → segmentação → regras (registry plugável) → relatório JSON + terminal, com veredito.
- Módulos: `extractor.py`, `segmenter.py`, `report.py`, `verificador.py` (orquestrador+CLI) e `rules/` (`estrutural.py`, `preliminares.py`, `redistribuicao.py`, `teses.py`, `llm_stubs.py`).
- Interface comum `Regra` (`id`, `bloco`, `descricao`, `requer_llm`) + registry.
- Saída JSON por verificação:
  `{ id, bloco, descricao, status, mensagem, evidencia }`, com `status ∈ {OK, ERRO, VERIFICAR, INFO}`.
- Veredito: **REPROVADO** se houver qualquer `ERRO`; senão **APROVADO**. Código de saída 1/0.
- Testes em `pytest`, `README.md`, banco de casos `contestacao_03.pdf … 16.pdf` (14 peças) + `gabarito_contestacoes_03-16.md`.

**Primeira coisa a fazer:** inspecione esse pacote e descubra o ponto de entrada público. Prefira importar uma função que devolva a lista de resultados (ex.: algo como `verificar_minuta(caminho) -> (veredito, resultados)`). Se não houver uma função limpa, **chame a CLI existente** capturando o JSON de saída. Não altere as regras nem o cálculo do veredito.

---

## Stack

- **Backend:** FastAPI (upload de arquivo, roda o verificador, serve o frontend buildado).
- **Localização de evidência:** PyMuPDF (`fitz`).
- **Frontend:** React + Vite + PDF.js (`pdfjs-dist`) + Tailwind. Overlay de grifos com `<div>` posicionados em absoluto sobre o canvas da página.
- **Sem chamadas externas / sem CDN.** Tudo empacotado e rodando em `localhost`. O contexto é jurídico/governamental e há preocupação com soberania de dados — nada de recurso remoto, nenhuma telemetria. O PDF nunca sai da máquina.
- Todo código, comentários, identificadores e textos de UI em **português (pt-BR)**.

Se algo do stack conflitar com o que já existe no repo, adapte-se ao que existe em vez de reescrever.

---

## Arquitetura

### Backend (FastAPI)

- `POST /api/verificar` — recebe o arquivo (multipart). Fluxo:
  1. Salva o upload em pasta temporária.
  2. Chama o verificador existente → obtém `veredito` + lista de `resultados`.
  3. Para cada resultado com `status ∈ {ERRO, VERIFICAR}` **e** com `evidencia` textual, chama o `localizador` (abaixo) para obter as coordenadas na página.
  4. Devolve o JSON do **Contrato de dados** (mais abaixo).
- `GET /api/minuta/{id}` — devolve os bytes do PDF original (ou inclua-o como base64 na resposta de `/verificar`). O frontend precisa renderizar **o mesmo PDF** de onde as coordenadas foram extraídas.
- Servir o frontend buildado como estático.

### `localizador.py` (módulo novo — o coração do recurso de grifar)

Assinatura sugerida:

```python
def localizar(pdf_path: str, texto_evidencia: str) -> list[dict]:
    """
    Retorna [{ "pagina": int, "rect": [x0, y0, x1, y1] }, ...]
    com coordenadas NORMALIZADAS (0.0–1.0) em relação à largura/altura da página.
    Lista vazia se não encontrar.
    """
```

Estratégia (robustez importa — o texto extraído raramente bate 100% com o layout):

1. Para cada página, tente `page.search_for(texto_evidencia)`.
2. Se vazio, **normalize espaços/quebras de linha** (colapse whitespace) e tente de novo.
3. Se ainda vazio, quebre a evidência em âncoras (frases/trechos distintivos) e busque a **maior âncora** que aparecer; devolva os retângulos encontrados.
4. Converta cada `Rect` (em pontos, origem no topo-esquerda) para **coordenadas normalizadas** dividindo por `page.rect.width` / `page.rect.height`. Devolva também as dimensões da página.
5. Se nada for encontrado, retorne lista vazia — **não invente posição**.

Use coordenadas normalizadas (0–1) de propósito: isso elimina qualquer descasamento de escala/unidade entre o PyMuPDF e o PDF.js no frontend. Assuma páginas sem rotação (é o caso de PDF exportado do SAPIENS); se detectar rotação, apenas registre em log e siga.

**Regras de ausência não são localizáveis.** Muitos erros são "campo obrigatório faltando" (ex.: NB, DER, endereçamento errado) — não há texto para grifar. Para esses, marque `localizavel: false`; eles aparecem só no painel lateral. Não force um grifo.

---

## Recurso principal: tela do PDF com erros grifados

Layout em duas colunas (responsivo; empilha no mobile):

- **Esquerda — visualizador do PDF:** renderiza todas as páginas com PDF.js. Sobre cada página, desenhe overlays absolutos para cada destaque daquela página: `left = x0 * larguraRenderizada`, `top = y0 * alturaRenderizada`, e assim por diante (coordenadas já normalizadas). Cada overlay:
  - cor por status: **ERRO = vermelho**, **VERIFICAR = âmbar/amarelo**, translúcido (opacidade ~0.35) para o texto continuar legível;
  - um pequeno rótulo com o **código da regra** (ex.: `B3.2`) no canto do grifo;
  - `id` compartilhado com o item correspondente no painel.
- **Direita — painel de diagnóstico:**
  - **banner de veredito** no topo: APROVADO (verde) / REPROVADO (vermelho), com contadores (nº de ERRO / VERIFICAR / OK / INFO);
  - lista **agrupada pelos 7 blocos** (1 Estrutural, 2 Preliminares, 3 Agentes nocivos, 4 Averbação, 5 Pedidos acessórios, 6 Redistribuição, 7 Indeferimento forçado);
  - cada item mostra: badge de status, código da regra, `descricao`, `mensagem` e, se houver, `evidencia`;
  - **clicar num item localizável** rola o PDF até o grifo e faz o overlay "pulsar" (destaque momentâneo). Itens não localizáveis mostram um ícone/nota "sem posição no documento".
  - filtro: alternar "só ERRO" / "todos os status".

Detalhe de UX: ao passar o mouse sobre um grifo no PDF, destaque o item correspondente no painel (e vice-versa).

---

## Contrato de dados (resposta de `/api/verificar`)

```json
{
  "veredito": "REPROVADO",
  "resumo": { "erro": 3, "verificar": 2, "ok": 18, "info": 1 },
  "paginas": [ { "numero": 1, "largura": 595, "altura": 842 } ],
  "resultados": [
    {
      "regra_id": "B3.2",
      "bloco": 3,
      "descricao": "Ruído: limiar aplicável ao período",
      "status": "ERRO",
      "mensagem": "Aplicou 90 dB(A) a período posterior a 19/11/2003 (limiar correto: 85).",
      "evidencia": "nível de ruído de 90 dB(A) no período de 2005 a 2010",
      "localizavel": true,
      "destaques": [
        { "pagina": 1, "rect": [0.12, 0.44, 0.71, 0.47] }
      ]
    },
    {
      "regra_id": "B1.1",
      "bloco": 1,
      "descricao": "Campo obrigatório: NB",
      "status": "ERRO",
      "mensagem": "Número do benefício (NB) ausente.",
      "evidencia": "",
      "localizavel": false,
      "destaques": []
    }
  ]
}
```

`rect` sempre em coordenadas normalizadas `[x0, y0, x1, y1]` (0–1). Os campos `regra_id`, `bloco`, `descricao`, `status`, `mensagem`, `evidencia` vêm **diretamente do verificador existente** — não os recalcule.

---

## Galeria de exemplos (opcional, mas recomendado para a demo)

Adicione uma tela inicial "Exemplos" que lista as 14 peças de teste (`contestacao_03.pdf … 16.pdf`) já presentes no repo, para clicar e ver o diagnóstico sem precisar subir arquivo. Se o `gabarito_contestacoes_03-16.md` for facilmente parseável, mostre lado a lado o **veredito esperado × veredito obtido** (indicador verde/vermelho de acerto). Isso vende a demo sozinho.

---

## Princípios inegociáveis

1. **Reutilize o verificador. Não reimplemente regras nem o veredito.** Sua camada só orquestra, localiza evidência e desenha.
2. **Degradação graciosa:** evidência não encontrada → item aparece no painel sem grifo, nunca com posição inventada.
3. **Zero rede externa.** Nada de CDN, fontes remotas, analytics. PDF.js e tudo mais empacotados localmente.
4. **pt-BR** em todo lugar.
5. **Não** entre nas áreas de credencial/pagamento/permissão — é um app local de leitura e diagnóstico.

---

## Entregáveis

- `web/` (ou pasta equivalente) com backend FastAPI + frontend React/Vite, **sem tocar** na lógica de regras do pacote existente.
- `localizador.py` com testes em `pytest` (inclua ao menos um caso de evidência encontrada e um de evidência inexistente).
- `README` da Fase 2: como instalar dependências e subir tudo com **um comando** (ex.: um script que faz build do frontend e sobe o FastAPI), mais um GIF/prints do fluxo.
- Não introduza dependências além do necessário; registre as que adicionar.

## Critérios de aceitação

- Subir uma minuta com erro de ruído/calor produz **veredito REPROVADO** e o trecho errado aparece **grifado em vermelho no PDF**, com o mesmo código de regra no painel.
- Clicar no item do painel rola até o grifo e o destaca.
- Um erro de campo ausente aparece no painel marcado como "sem posição no documento", sem grifo falso.
- Uma minuta correta produz **APROVADO** sem grifos de erro.
- O app roda 100% offline em `localhost`.

## Como começar

1. Leia o pacote `verificador-contestacao/` e identifique o ponto de entrada (função ou CLI que devolve o JSON de resultados).
2. Escreva `localizador.py` + seus testes primeiro (é a parte com mais risco técnico).
3. Suba o backend FastAPI reaproveitando o verificador.
4. Construa o frontend com o visualizador de PDF e o painel.
5. Ligue a galeria de exemplos por último.

Comece confirmando, em 3–5 linhas, como pretende invocar o verificador existente e onde vai encaixar o `localizador`, antes de escrever o resto do código. A partir daí, avance com autonomia — mas, a cada arquivo criado ou alterado, **mostre o código e explique em uma ou duas linhas o que mudou e por quê.**
