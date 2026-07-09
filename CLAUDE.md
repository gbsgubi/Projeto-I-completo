# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Visão geral

Verificador de **minutas de contestação** do INSS em ações previdenciárias de
**aposentadoria especial**, usado pelo estagiário antes de enviar a peça ao
procurador. A minuta é gerada no SAPIENS (AGU) a partir do modelo padrão
nº 544316 (nativamente HTML, tipicamente exportada como PDF).

A arquitetura tem duas camadas:

| Camada | Estado | Onde |
|--------|--------|------|
| **Fase 1 — determinística** | implementada | `verificador-contestacao/` (CLI Python; regex + aritmética de datas; sem rede, sem ML) |
| **Fase 2 — raciocínio (LLM)** | apenas stubs | `verificador-contestacao/src/rules/llm_stubs.py` |

Além do CLI há um **app web de demonstração** (`web/`, FastAPI + React/Vite/
Tailwind) que roda o verificador e **grifa cada erro no lugar exato do PDF**.

Código, comentários, mensagens, commits e documentação são **em português**.

## Mapa do repositório

```
Projeto-I-completo/
├── CLAUDE.md
├── regras_verificacao_contestacao.md   # ESPECIFICAÇÃO das regras (blocos 1–7) — fonte da verdade jurídica
├── gabarito_contestacoes_03-16.md      # gabarito do banco de testes (hoje cobre 03–17)
├── gabarito_minuta_teste.md            # gabarito da minuta de teste (fixtures do pytest)
├── contestacao_03.pdf … contestacao_18.pdf   # banco de peças sintéticas de teste
├── Contestação1..3.{pdf,docx}, minuta_teste.{pdf,html,docx}  # peças da fase inicial
├── resultado_contestacao*.tex, relatorio_unificado.tex       # relatórios LaTeX gerados
├── saida/                              # gerar_tex.py + saídas (json/txt/err) por contestação
├── prompt_claude_code_fase1.md, prompt_app_demo_verificador.md  # prompts que originaram as fases
├── verificador-contestacao/            # ===== FASE 1 (CLI) =====
│   ├── README.md                       # documentação detalhada da Fase 1
│   ├── demo.ps1                        # demo de um clique (venv + deps + roda na minuta de teste)
│   ├── requirements.txt                # pdfplumber, beautifulsoup4, pytest
│   ├── .venv/                          # venv PRÓPRIO da Fase 1 (fora do git)
│   ├── src/  (pipeline + regras — ver "Arquitetura")
│   ├── tests/ (pytest + fixtures minuta_teste.pdf/.html)
│   └── examples/, docs/
└── web/                                # ===== APP DEMO (Fase 2 visual) =====
    ├── README.md                       # documentação detalhada do app
    ├── run.ps1                         # sobe tudo com um comando (localhost:8000)
    ├── .venv/                          # venv PRÓPRIO do web (fora do git)
    ├── backend/  (app.py, localizador.py, tests/)
    └── frontend/ (React + Vite + Tailwind + pdfjs-dist; dist/ fora do git)
```

Atenção: são **dois venvs separados** — `verificador-contestacao/.venv` (CLI) e
`web/.venv` (backend, que também instala as deps do CLI porque o importa).

## Comandos

### CLI do verificador (a partir de `verificador-contestacao/`)

```powershell
.venv\Scripts\python.exe -m src.verificador ..\contestacao_17.pdf     # relatório legível
.venv\Scripts\python.exe -m src.verificador minuta.html               # HTML nativo do SAPIENS
.venv\Scripts\python.exe -m src.verificador minuta.pdf --json out.json  # grava JSON
.venv\Scripts\python.exe -m src.verificador minuta.pdf --so-json      # só JSON no stdout
```

Código de saída: **1 = REPROVADO, 0 = APROVADO** (útil em automações);
2 = erro de uso (arquivo inexistente/formato não suportado).

### Testes da Fase 1 (a partir de `verificador-contestacao/`)

```powershell
.venv\Scripts\python.exe -m pytest -q                                  # suíte inteira
.venv\Scripts\python.exe -m pytest tests\test_regras_deterministicas.py -q   # um arquivo
.venv\Scripts\python.exe -m pytest -q -k test_ruido_90db               # um teste (por -k)
```

### Validação contra o banco de testes (obrigatória após mexer em regras)

Não há script commitado; o padrão usado é um loop inline:

```python
# a partir de verificador-contestacao/, com o venv da Fase 1
import sys; sys.path.insert(0, '.')
from src.verificador import verificar_minuta
for n in ['03','04','05','06','07','08','09','10','11','12','13','14','15','16','17']:
    r = verificar_minuta(f'../contestacao_{n}.pdf')
    print(n, r.veredito, len(r.erros), len(r.verificar))
```

Compare com a tabela "Vereditos esperados" abaixo — **veredito E contagem**.

### App web

```powershell
powershell -ExecutionPolicy Bypass -File .\web\run.ps1        # build (se preciso) + localhost:8000
powershell -ExecutionPolicy Bypass -File .\web\run.ps1 -Rebuild -Porta 8080

# modo desenvolvimento
cd web\backend;  ..\.venv\Scripts\python.exe -m uvicorn app:app --port 8000 --reload
cd web\frontend; npm run dev                                   # hot-reload, proxy /api -> 8000

# testes do backend web (a partir de web/)
.venv\Scripts\python.exe -m pytest backend\tests\ -q

# só rebuildar o frontend (a partir de web/frontend/)
npm run build
```

O frontend é servido do build em `web/frontend/dist/` (**ignorado pelo git**):
mudança em `web/frontend/src/` só aparece após `npm run build` ou `run.ps1 -Rebuild`.

## Arquitetura da Fase 1

### O critério que governa tudo (decisão de projeto do usuário)

Uma regra determinística só emite `ERRO` quando o defeito é **certo** a partir
do texto da própria minuta (casamento de padrões + aritmética de datas). Se a
certeza exigir contexto externo (petição inicial, PA) ou raciocínio (ex.:
período que **cruza** um marco temporal), a regra emite no máximo `VERIFICAR`
e a decisão fica para a Fase 2. Os stubs de LLM seguem a mesma interface
`Regra` mas **não são registrados** — o CLI apenas os lista no rodapé como
"verificações adiadas". **Não promova um stub a regra determinística sem esse
grau de certeza.**

### Pipeline (`verificador-contestacao/src/`)

```
caminho.pdf/.html
  → extractor.py   pdfplumber (PDF) / BeautifulSoup (HTML)
                   → DocumentoExtraido { caminho, formato, texto,
                                         destaques_amarelos[], suporta_amarelo }
  → segmenter.py   divide por títulos ("SÍNTESE DA DEMANDA", "PRELIMINARES",
                   "DO MÉRITO", "OUTROS FUNDAMENTOS", "DOS PEDIDOS") e extrai
                   blocos de período do mérito
                   → Minuta { texto, secoes{cabecalho|sintese|preliminares|merito|
                              outros_fundamentos|pedidos},
                              periodos[{inicio, fim, agente, texto}] }
  → rules/         cada regra recebe a Minuta e devolve [Resultado]
  → report.py      Resultado { id, bloco, descricao, status, mensagem, evidencia }
                   status ∈ {OK, ERRO, VERIFICAR, INFO}
                   Relatorio.veredito = REPROVADO se houver QUALQUER ERRO
  → verificador.py orquestrador + CLI (main)
```

- O cabeçalho de período casado pelo segmenter é
  `"Período de dd/mm/aaaa a dd/mm/aaaa - Agente: X"` (linha única); o campo
  `texto` de cada período vai até o próximo cabeçalho.
- `utils.normalizar()` → minúsculas, sem acentos (NFKD), espaços colapsados.
  `utils.primeiro_trecho()` → trecho do texto ORIGINAL com contexto, usado como
  `evidencia`.

### Registry e como adicionar uma regra

1. Subclasse de `Regra` (em `src/rules/__init__.py`: atributos `id`, `bloco`,
   `descricao`; método `verificar(minuta) -> list[Resultado]`).
2. Decore com `@registrar`.
3. Garanta que o módulo é importado em `verificador.py` (o import dispara o
   registro; módulos novos precisam entrar na lista de imports).
4. Preencha `evidencia` com `primeiro_trecho()` sempre que o achado tiver
   posição no documento — **o app web usa a evidência como âncora do grifo no
   PDF**; sem evidência o item aparece como "sem posição no documento".
5. Escreva testes: minutas sintéticas sem PDF via
   `DocumentoExtraido(caminho=..., formato="pdf", texto=...)` + `segmentar()`
   (padrão em `tests/test_regras_deterministicas.py`).

### Catálogo das regras determinísticas (ids estáveis)

**`estrutural.py` — Bloco 1**
- `1.1-enderecamento` — JEF × Justiça Federal comum (INFO; VERIFICAR se indeterminado).
- `1.2-campos-obrigatorios:*` — NB, DER, nº do processo (regex CNJ), nome do
  autor ("que lhe move NOME"), tipo de benefício → ausente = ERRO.
- `1.3-marcacoes-edicao` — colchetes `[...]` (sem quebra de linha), `XXXX`,
  `____` (linha de assinatura ignorada), instruções remanescentes (VERIFICAR/
  ATENÇÃO/PREENCHER/…), destaque amarelo (só HTML) → qualquer achado = ERRO.

**`preliminares.py` — Bloco 2**
- `2.0-presenca-preliminares` (`2.presenca:<id>`) — cataloga PRESENTE/AUSENTE
  de 10 preliminares (INFO, nunca erro).
- `2.12-preliminares-sempre-obrigatorias` (`2.1-juizo-digital-obrigatoria`,
  `2.2-conciliacao-obrigatoria`) — Juízo 100% Digital e Audiência de
  Conciliação ausentes = ERRO (sempre obrigatórias).
- `2.3-renuncia-jef` — bidirecional: ausente no JEF = ERRO; presente na JF
  comum = ERRO; endereçamento indeterminado = VERIFICAR.
- `2.4-decadencia-datas` — decadência PRESENTE com `ano_ajuizamento − ano_DER
  < 10` = ERRO (prazo impossível: a 1ª prestação nunca antecede a DER). Ano de
  ajuizamento: "ajuizada em AAAA" ou o campo AAAA do número CNJ. Diferença
  exatamente 10 = VERIFICAR; ≥ 10 = INFO. Decadência AUSENTE quando cabível =
  Fase 2.

**`agentes.py` — Bloco 3 (determinístico)**
- `3.5-ruido-limiar:<inicio>` — limite de tolerância por janela: ≤05/03/1997 →
  80 dB; 06/03/1997–18/11/2003 → 90 dB; ≥19/11/2003 → 85 dB(A) NEN. Período
  inteiro numa janela + valor errado = ERRO; período cruzando marco = VERIFICAR.
- `3.5-ruido-metodologia:<inicio>` — período inteiro ≥19/11/2003 citando NR-15
  sem NEN/NHO-01 = ERRO; NR-15 para período ≤18/11/2003 = OK.
- `3.6-calor-limiar:<inicio>` — ≤05/03/1997 → 28 ºC; 06/03/1997–10/12/2019 →
  25 ºC; ≥11/12/2019 → 24,7 ºC. Mesma lógica de janela única.
- `3.3-vicio-crea-crm` — qualquer menção `\b(crea|crm)\b` = ERRO (vício abolido
  pelo manual).
- `3.17-vedacao-conversao` — período com fim > 13/11/2019 sem menção à vedação
  ("vedada a conversão"/"vedação à conversão") = ERRO. **A presença da vedação
  sem período que a exija NÃO é erro** (fundamento padrão tolerado — decisão do
  gabarito da minuta de teste).
- `3.1-consistencia-sintese-tabela` (`:omitidos`, `:nao-pedidos`) — pares
  `de dd/mm/aaaa a dd/mm/aaaa` da SÍNTESE × períodos da tabela do mérito;
  divergência = 1 ERRO por direção. Só roda quando ambos os lados têm datas.
  (A cobertura contra a petição inicial em si, externa, é Fase 2.)

**`redistribuicao.py` — Bloco 6** (gradação sinal forte × fraco)
- `6.1-vigilante`, `6.2-saude`, `6.3-professor` — termo declarado na **síntese
  ou no campo "Agente:"** (sinal forte) = ERRO (contestação padrão indevida;
  redistribuir); termo solto em outro trecho = INFO (sugestão). Saúde exige
  também menção a agente biológico; professor exige ano > 1981 no texto.
- `6.4-sem-pedido-tempo-especial` — síntese declarando que a inicial não pede
  tempo especial = ERRO (redistribuir).

**`indeferimento.py` — Bloco 7**
- `7.1-indeferimento-forcado` — texto registrando `Possui tempo especial? "Não"`
  + "não houve análise técnica" = ERRO (deveria usar a minuta nº 618527, não a
  contestação padrão 544316). Sem esses sinais no texto = INFO (a informação
  vive no PA).

**`teses.py`**
- `345-catalogo-teses` — cataloga teses padronizadas (`CTN-*`, `DIVESP-*`) presentes (INFO).

**`llm_stubs.py` — Fase 2 (NÃO registrados)**
- `3.x-compat-tese-agente-periodo` — períodos cruzando marcos + demais agentes
  (biológico, químico, eletricidade, …).
- `2.8-situacoes-ppp` — as três situações de PPP não apresentado (exige PA).
- `2.45-decadencia-prescricao-datas` — decadência ausente quando cabível,
  concessão × revisão, prescrição.
- `1.4-cobertura-periodos-inicial` — cobertura contra a petição inicial (externa).

### Vereditos esperados do banco de testes (calibração)

| Peça | Veredito | Erros | Observação |
|------|----------|-------|------------|
| 03, 04, 07, 16 | APROVADO | 0 | corretas (04 é JF comum sem renúncia; 16 tem vedação no pedido "c") |
| 05 | REPROVADO | 2 | decadência por datas + colchete `[VERIFICAR: …]` |
| 06 | REPROVADO | 3 | ruído limiar + metodologia + falta vedação |
| 08 / 09 / 10 | REPROVADO | 1 | redistribuição vigilante / saúde / professor |
| 11 | REPROVADO | 1 | indeferimento forçado (os sinais estão embutidos na peça) |
| 12 | REPROVADO | 2 (+1 VERIFICAR) | NB ausente + sem pedido de tempo especial; ruído 1990–98 cruza marco → VERIFICAR |
| 13 | REPROVADO | 3 | omite período + impugna não pedido + **falta vedação (erro extra legítimo, não listado no gabarito)** |
| 14 | REPROVADO | 2 | CREA/CRM + calor 24,7 ºC em janela de 25 ºC |
| 15 | REPROVADO | 2 | faltam 100% Digital e Renúncia 60 SM (JEF) |
| 17 | REPROVADO | **7** | peça-síntese de aceitação (NB, 100% Digital, decadência, ruído ×2, CREA/CRM, vedação) |
| 18 | APROVADO | 0 (+1 VERIFICAR) | ainda sem linha no gabarito |
| minuta_teste | REPROVADO | 2 | marcação de edição + decadência por datas; ruído na fronteira 03/12/1998 = Fase 2 |

## Arquitetura do app web (`web/`)

### Backend (`backend/app.py`, FastAPI)

- Importa `src.verificador.verificar_minuta` **diretamente** (via
  `sys.path.insert` apontando para `verificador-contestacao/`). **Princípio
  nº 1: a interface nunca reimplementa regra** — veredito e resultados vêm
  100% da Fase 1; regra nova entra no app automaticamente.
- Endpoints:
  - `POST /api/verificar` (upload `.pdf`/`.html`) → contrato:
    `{ minuta_id, tipo, veredito, resumo{erro,verificar,ok,info}, paginas[],
       resultados[{regra_id, bloco, descricao, status, mensagem, evidencia,
       localizavel, destaques[{pagina, rect[x0,y0,x1,y1] normalizados 0–1}]}] }`
  - `GET /api/minuta/{id}` → serve o arquivo original ao viewer.
  - `GET /api/exemplos` → lista `contestacao_*.pdf` da raiz + veredito esperado
    parseado da tabela markdown do gabarito (regex de linha
    `| NN | APROVAR/REPROVAR | motivo |`). Peça nova aparece automaticamente,
    mas só ganha "esperado" com linha na tabela.
  - `POST /api/exemplos/{numero}/verificar` → roda a Fase 1 numa peça do banco
    (`minuta_id = "exemplo-NN"`).
- Ganham grifo: `ERRO`, `VERIFICAR` e os INFO de "Redistribuição sugerida"
  (função `_deve_localizar`). Uploads vivem em pasta temporária do processo.

### Localizador (`backend/localizador.py`, PyMuPDF)

Converte a `evidencia` textual em retângulos: tenta `page.search_for` com o
trecho completo → busca com espaços colapsados → casamento de tokens
normalizados contra `page.get_text("words")` (maior âncora contígua — as
evidências chegam recortadas no meio de palavras). Coordenadas normalizadas
pela largura/altura da página; evidência não encontrada → lista vazia → item
"sem posição no documento" (**nunca inventar grifo**).

### Frontend (`frontend/src/`, React + Vite + Tailwind v4 + pdfjs-dist)

```
App.jsx                      # header/rodapé; alterna TelaInicial × Diagnostico;
                             # deep-link ?exemplo=NN abre direto o diagnóstico
api.js                       # fetch dos endpoints
constantes.js                # cores dos grifos + badges/glifos/acentos por status
componentes/
├── TelaInicial.jsx          # hero + zona de upload (drag & drop) + Galeria
├── Galeria.jsx              # cards esperado × obtido, indicador ✓/✘,
│                            # resumo "N/M de acordo com o gabarito"
├── Diagnostico.jsx          # barra superior + 2 colunas (PDF | painel sticky)
├── VisualizadorPdf.jsx      # canvas PDF.js (worker empacotado, sem CDN) +
│                            # overlays em % com rótulo do regra_id
└── PainelDiagnostico.jsx    # banner veredito, stat tiles, filtro segmentado,
                             # itens agrupados por bloco (hover/click sincronizado
                             # com os grifos)
```

Convenções visuais: status **nunca é só cor** — badges carregam glifo
(✕/!/✓/i) + rótulo; números dos contadores em tinta neutra; overlays vermelho =
ERRO, âmbar = VERIFICAR, azul = redistribuição (INFO). Restrição dura: **100%
offline** — nenhuma fonte externa, CDN ou telemetria; ícones são SVG inline ou
emoji; fonte de sistema.

## Pegadinhas conhecidas

- **`normalizar()` e o "º"**: NFKD decompõe "º" (ordinal) em "o" — `"25 ºC"`
  normaliza para `"25 oc"` (e "°" degree sign simplesmente some → `"25 c"`).
  Regexes sobre texto normalizado precisam aceitar `o?\s*c`. Esse detalhe já
  silenciou a regra de limiar de calor uma vez.
- **`\bnen\b` exige word boundary**: "nen" é substring de "permanente",
  "nenhum" etc.
- **Ano CNJ = ano de ajuizamento**: `NNNNNNN-DD.AAAA.J.TR.OOOO` — o AAAA é
  usado pela regra de decadência quando não há "ajuizada em AAAA" no texto.
- **Colchetes multilinhas escapam da 1.3**: o padrão de colchetes não cruza
  linha (`[^\]\n]`); o bloco `[Análise do PA: …]` da peça 11 se estende por
  duas linhas e por isso NÃO é pego como marcação de edição (o erro da 11 vem
  da regra 7.1).
- **Screenshot headless do app**: Edge/Chromium com `--virtual-time-budget`
  congela o relógio que o worker do PDF.js usa — o PDF fica em "Carregando…"
  para sempre. Para verificação visual use CDP com espera em tempo real
  (`--remote-debugging-port` + `Page.captureScreenshot`) ou apenas confira o
  painel (que renderiza sem PDF).
- **Warnings LF→CRLF no git** são normais no Windows e inofensivos.

## Fluxo de trabalho ao mexer em regras

1. Escreva/ajuste a regra seguindo o critério de certeza (ERRO só quando certo).
2. `pytest -q` na Fase 1 (45+ testes) — inclui minutas sintéticas por string.
3. Rode o loop de validação contra `contestacao_03..17.pdf` e confira veredito
   **e contagem de erros** com a tabela acima; as 4 corretas (03/04/07/16) não
   podem ganhar falso positivo.
4. Se o comportamento esperado de uma peça mudar de propósito, atualize
   `gabarito_contestacoes_03-16.md` (tabela **e** seção detalhada) — a galeria
   do app lê a tabela.
5. Se a regra emitir evidência nova, confira no app web que o grifo aparece
   (`run.ps1` → clicar no item) — evidências muito curtas ou muito recortadas
   podem não ancorar.
6. Testes do backend web: `web\.venv\Scripts\python.exe -m pytest backend\tests\ -q`.
