# Prompt para Claude Code — Fase 1: Script de Verificação Determinística

> Copie o conteúdo abaixo (a partir de "INÍCIO DO PROMPT") para o Claude Code.
> Antes de rodar, coloque na pasta de trabalho os seguintes arquivos de apoio (fornecidos à parte):
> - `regras_verificacao_contestacao.md` (a especificação completa das regras)
> - `minuta_teste.pdf` e `minuta_teste.html` (exemplo de entrada)
> - `gabarito_minuta_teste.md` (o resultado esperado para o exemplo)

---

## INÍCIO DO PROMPT

### Contexto do projeto

Estou construindo uma ferramenta que verifica **minutas de contestação** em ações
previdenciárias de aposentadoria especial, antes de o estagiário enviá-las ao procurador. A
minuta é gerada no sistema SAPIENS (da AGU) a partir de um modelo padrão (nº 544316), é
nativamente HTML e tipicamente exportada como PDF. A ferramenta recebe essa minuta e devolve um
diagnóstico de aprovação ou reprovação, apontando os problemas.

A arquitetura final terá uma camada determinística (script puro) e uma camada de raciocínio
(LLM). **Nesta fase, você vai construir APENAS a camada determinística.** Não use nenhum modelo
de linguagem, biblioteca de machine learning ou chamada de API. Tudo deve ser regra explícita,
auditável e testável.

Leia o arquivo `regras_verificacao_contestacao.md` na raiz do projeto: ele contém a
especificação completa das regras em 7 blocos. Nesta fase você implementará somente as
verificações que são de presença/ausência e de padrão textual (detalhadas abaixo). As
verificações que exigem raciocínio contextual ficam para depois e devem apenas ser deixadas como
pontos de extensão (interfaces/stubs documentados).

### Objetivo desta fase

Um script de linha de comando que:
1. Recebe o caminho de uma minuta (`.pdf` ou `.html`).
2. Extrai e segmenta o texto.
3. Aplica as verificações determinísticas.
4. Emite um relatório estruturado (JSON + versão legível no terminal).

### Escopo — o que ENTRA nesta fase

Implemente apenas estas verificações determinísticas:

**Bloco 1 — Estrutural**
- Detectar o tipo de endereçamento: JEF (contém "JUIZADO ESPECIAL FEDERAL") ou Justiça Federal
  comum. Reportar qual foi identificado; se não der para determinar, marcar como VERIFICAR.
- Verificar presença dos campos obrigatórios via regex: NB, DER, número do processo, nome do
  autor, e tipo de benefício (concessão/revisão/aposentadoria especial/etc.). Reportar cada um
  como presente ou ausente.
- Detectar marcações de edição não removidas: trechos com colchetes `[...]`, sequências de
  placeholder (`XXXX`, `____`), e instruções imperativas remanescentes (ex.: palavras como
  "VERIFICAR", "ATENÇÃO", "deixar a preliminar"). No caso de entrada HTML, detectar também
  elementos com destaque amarelo (ex.: classe CSS `amarelo`, `style` com `background` amarelo).

**Bloco 2 — Preliminares (somente PRESENÇA, não a lógica condicional)**
- Para cada preliminar, detectar se está presente no texto, por nome de tese padronizado e/ou por
  trecho característico: Juízo 100% Digital, Audiência de Conciliação, Renúncia aos 60
  salários-mínimos, Decadência, Prescrição, Coisa Julgada, Litispendência, PPP não apresentado
  administrativamente, Períodos reconhecidos administrativamente, Petição inicial inepta.
- Reportar cada uma como PRESENTE ou AUSENTE. Não decidir ainda se *deveria* estar presente
  (isso depende de contexto e fica para a fase do LLM) — apenas registrar o fato.
- Exceção determinística simples: se o endereçamento é JEF e a preliminar de Renúncia aos 60 SM
  está ausente, marcar como ERRO (essa correlação é puramente estrutural).

**Bloco 6 — Redistribuição**
- Detectar, no contexto de categoria profissional, os termos que disparam redistribuição:
  "vigilante", "vigia", "guarda", "policial" → flag VIGILANTE.
- Detectar indício de profissional de saúde (ex.: "enfermeiro", "médico", "auxiliar de
  enfermagem", "hospital", "estabelecimento de saúde") combinado com menção a agente biológico →
  flag SAÚDE.
- Detectar "professor" com indício de período posterior a 1981 → flag PROFESSOR.
- Cada flag deve ser reportada como "redistribuição sugerida", não como erro.

**Teses presentes (Blocos 3, 4 e 5 — somente CATALOGAÇÃO)**
- Extrair e listar todas as teses padronizadas presentes no texto (padrão de nome começando por
  `CTN-`, `DIVESP-NOTA-`, etc.). Apenas catalogar quais aparecem. **Não** avaliar ainda se a tese
  é compatível com o agente/período (isso é da fase do LLM).

### Escopo — o que NÃO entra nesta fase (deixar como pontos de extensão)

Não implemente, mas deixe interfaces/stubs documentados para:
- Compatibilidade entre tese, período e agente nocivo (lógica dos marcos temporais de ruído,
  calor, etc.).
- Distinção entre as três situações de PPP não apresentado.
- Lógica condicional de decadência/prescrição baseada em datas e tipo de ação.
- Cobertura de períodos da petição inicial (exige ler a inicial, que não está na minuta).

### Formato de entrada

- **PDF** (principal): use `pdfplumber` ou `PyMuPDF` para extrair texto e tabelas.
- **HTML** (secundário): use `BeautifulSoup`. O HTML preserva a estrutura semântica e permite
  detecção direta de destaques amarelos.
- A segmentação em seções deve ser por palavras-chave/títulos (ex.: "PRELIMINARES", "DO MÉRITO",
  "Período(s):", "Fundamentos da defesa"), de forma robusta a pequenas variações.

### Formato de saída

Relatório estruturado, com duas representações:
1. **JSON** — uma lista de verificações, cada uma com:
   `{ id, bloco, descricao, status, mensagem, evidencia }`
   onde `status` ∈ `{ "OK", "ERRO", "VERIFICAR", "INFO" }` e `evidencia` é o trecho do texto que
   embasou a conclusão (com posição/seção quando possível).
2. **Terminal** — versão legível, agrupada por bloco, com um veredito final no topo
   (APROVADO / REPROVADO) e contagem de erros e pontos de verificação.

Regra do veredito: REPROVADO se houver qualquer `ERRO`; caso contrário APROVADO, mas listando os
`VERIFICAR` pendentes.

### Estrutura do projeto

Crie a seguinte estrutura (ajuste nomes se fizer sentido, mantendo a modularidade):

```
verificador-contestacao/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── extractor.py          # extração de texto/tabelas (PDF e HTML)
│   ├── segmenter.py          # identificação de seções da minuta
│   ├── report.py             # modelo de resultado + serialização JSON/terminal
│   ├── verificador.py        # orquestrador + CLI (entry point)
│   └── rules/
│       ├── __init__.py       # registro/coleta das regras
│       ├── estrutural.py     # Bloco 1
│       ├── preliminares.py   # Bloco 2 (presença)
│       ├── redistribuicao.py # Bloco 6
│       └── teses.py          # catalogação de teses (Blocos 3/4/5)
├── tests/
│   ├── fixtures/
│   │   ├── minuta_teste.pdf
│   │   └── minuta_teste.html
│   └── test_*.py
└── examples/
    └── (saídas de exemplo)
```

### Princípios de design

- Cada regra deve ser uma função/objeto isolado, com entrada (texto segmentado) e saída
  (resultado de verificação) bem definidas, fácil de testar unitariamente.
- Use um registro de regras (lista/registry) para que adicionar uma nova regra não exija mexer no
  orquestrador.
- Projete pensando na futura camada de LLM: defina uma interface comum de "regra" que tanto as
  determinísticas quanto as futuras (baseadas em LLM) possam implementar. Os stubs do que fica
  para depois devem seguir essa mesma interface.
- Sem dependência de rede, sem LLM, sem ML nesta fase.
- Código e comentários em português; nomes de identificadores podem ser em português.

### Validação

Use os arquivos de teste fornecidos:
- `tests/fixtures/minuta_teste.pdf` e `.html` são a entrada de exemplo.
- `gabarito_minuta_teste.md` descreve o resultado esperado.

Escreva testes (pytest) que confirmem, no mínimo, que o script:
- Identifica o endereçamento como JEF.
- Extrai NB, DER, processo e autor.
- Detecta a marcação amarela / instrução não removida (deve gerar ERRO).
- Reporta as preliminares presentes (Juízo Digital, Conciliação, Renúncia 60 SM, Decadência) e a
  ausente (Prescrição).
- Cataloga as teses presentes.
- Não gera falsos positivos nos itens que o gabarito marca como corretos.

Observe que, nesta fase, o script **não** precisa detectar o erro de compatibilidade da tese de
ruído (Erro 2 do gabarito) nem a inconsistência decadência/concessão (Erro 5) — esses dependem da
camada de LLM. Documente isso no README.

### Operação com git

Inicialize o repositório e versione desde o começo:
1. `git init` na raiz do projeto.
2. Crie um `.gitignore` adequado para Python (venv, `__pycache__`, `.pytest_cache`, etc.).
3. Faça commits pequenos e descritivos conforme avança (ex.: "estrutura inicial", "extrator de
   PDF", "regras estruturais", "regras de preliminares", "relatório", "testes").
4. Ao final, deixe o repositório pronto para receber um remoto, e me diga exatamente quais
   comandos rodar para criar o repositório no GitHub e dar o primeiro push (incluindo a opção via
   `gh` CLI, se disponível, e a opção manual via web + `git remote add`).

### Entregáveis desta fase

- O projeto completo na estrutura acima, com o script funcional rodando sobre a minuta de teste.
- README explicando: como instalar dependências, como rodar o script, o que ele verifica nesta
  fase, e o que ficou para a fase do LLM.
- Testes passando.
- Repositório git inicializado com histórico de commits e instruções de push.

Comece confirmando seu plano de implementação antes de escrever o código.

## FIM DO PROMPT
