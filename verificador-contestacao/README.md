# Verificador de Contestação — Fase 1 (camada determinística)

[![Repositório](https://img.shields.io/badge/GitHub-verificador--contestacao-181717?logo=github)](https://github.com/gbsgubi/verificador-contestacao)

Ferramenta de linha de comando que verifica **minutas de contestação** em ações
previdenciárias de aposentadoria especial, antes de o estagiário enviá-las ao
procurador. A minuta é gerada no SAPIENS (AGU) a partir do modelo padrão
(nº 544316), é nativamente HTML e tipicamente exportada como PDF.

A arquitetura final terá duas camadas: uma **determinística** (script puro) e
uma de **raciocínio** (LLM). **Esta fase implementa apenas a camada
determinística** — sem nenhum modelo de linguagem, biblioteca de ML ou chamada
de rede. Toda verificação é regra explícita, auditável e testável.

---

## O que a ferramenta verifica nesta fase

Tudo o que é decidível com **regex + aritmética de datas sobre o texto da
própria minuta**. O critério é estrito: se a certeza do erro exigir contexto
externo (petição inicial, PA) ou raciocínio (período que cruza marco
temporal), a regra **não** acusa `ERRO` — no máximo marca `VERIFICAR` e deixa
a decisão para a fase do LLM.

### Bloco 1 — Estrutural
- **1.1 Endereçamento**: identifica JEF (contém "JUIZADO ESPECIAL FEDERAL") ou
  Justiça Federal comum; se indeterminado, marca `VERIFICAR`.
- **1.2 Campos obrigatórios** (via regex): NB, DER, número do processo, nome do
  autor e tipo de benefício. Cada um reportado como presente (`OK`) ou ausente
  (`ERRO`).
- **1.3 Marcações de edição não removidas**: colchetes `[...]`, placeholders
  (`XXXX`, `____`), instruções imperativas remanescentes ("VERIFICAR",
  "ATENÇÃO", "deixar a preliminar", ...) e, no HTML, destaque amarelo (classe
  CSS `amarelo` ou `style` com fundo amarelo). Qualquer achado gera `ERRO`.
  A linha de assinatura (só sublinhados) é ignorada para evitar falso positivo.

### Bloco 2 — Preliminares
- Cataloga a **presença/ausência** de cada preliminar padronizada (INFO).
- **2.1/2.2 Sempre obrigatórias**: Juízo 100% Digital e Audiência de
  Conciliação ausentes → `ERRO`.
- **2.3 Renúncia aos 60 SM** (bidirecional): ausente no JEF → `ERRO`;
  presente na Justiça Federal comum → `ERRO`.
- **2.4 Decadência por datas**: preliminar presente quando `ano do
  ajuizamento − ano da DER < 10` → `ERRO` (o prazo de 10 anos é impossível,
  pois a primeira prestação nunca antecede a DER). O ano de ajuizamento vem de
  "ajuizada em AAAA" ou do campo AAAA do número CNJ. A decadência **ausente**
  quando cabível continua na fase do LLM.

### Bloco 3 — Tabela de agentes nocivos (determinístico)
- **3.5 Ruído — limite de tolerância**: 80 dB até 05/03/1997; 90 dB de
  06/03/1997 a 18/11/2003; 85 dB(A) NEN a partir de 19/11/2003. Valor errado
  com período inteiramente numa janela → `ERRO`; período cruzando marco →
  `VERIFICAR` (fase do LLM).
- **3.5 Ruído — metodologia**: NR-15 invocada para período inteiramente
  posterior a 18/11/2003 (sem NEN/NHO-01) → `ERRO`.
- **3.6 Calor — limiar**: 28 ºC até 05/03/1997; 25 ºC de 06/03/1997 a
  10/12/2019; 24,7 ºC a partir de 11/12/2019. Mesma lógica de janela única.
- **3.3 Vício CREA/CRM**: qualquer uso do vício de falta de registro no
  CREA/CRM → `ERRO` (o manual aboliu esse vício).
- **3.17 Vedação à conversão (EC 103/2019)**: período que ultrapassa
  13/11/2019 sem menção à vedação → `ERRO`. A presença da vedação sem período
  que a exija **não** é erro (fundamento padrão tolerado).
- **3.1 Consistência síntese × tabela**: períodos enumerados na síntese da
  demanda divergentes dos da tabela do mérito (omissão ou impugnação não
  pedida) → `ERRO`. A checagem contra a petição inicial em si fica no LLM.

### Bloco 6 — Redistribuição (com gradação)
- **VIGILANTE / SAÚDE / PROFESSOR pós-1981**: quando o perfil está declarado
  na **síntese ou no campo "Agente:"** da tabela (sinal forte), a contestação
  padrão é indevida → `ERRO`. Termo solto em outro trecho → apenas sugestão
  (INFO).
- **6.4 Sem pedido de tempo especial**: síntese declarando que a inicial não
  pede tempo especial → `ERRO` (caso de redistribuição).

### Bloco 7 — Indeferimento forçado
- **7.1**: se o próprio texto registra "Possui tempo especial? NÃO" + ausência
  de análise técnica, a contestação padrão é indevida → `ERRO` (deveria ser a
  minuta nº 618527). Sem esses sinais no texto, nada é acusado (a informação
  vive no PA).

### Teses presentes (Blocos 3/4/5 — CATALOGAÇÃO)
- Lista as teses padronizadas presentes (nomes começando por `CTN-`,
  `DIVESP-NOTA-`, etc.).

---

## O que ficou para a fase do LLM (pontos de extensão)

Estão documentados como stubs em [`src/rules/llm_stubs.py`](src/rules/llm_stubs.py),
seguindo a **mesma interface `Regra`** — basta implementá-los e registrá-los:

- **Compatibilidade tese × agente em períodos que cruzam marcos temporais**
  (ex.: ruído na fronteira de 03/12/1998 — **Erro 2** do gabarito da minuta de
  teste) e demais agentes (biológico, químico, eletricidade, ...).
- **Distinção entre as três situações de PPP não apresentado.**
- **Decadência ausente quando cabível, concessão × revisão e prescrição**
  (→ **Erro 4** do gabarito; o caso "decadência presente com prazo impossível"
  já é determinístico).
- **Cobertura dos períodos requeridos na petição inicial** (exige ler a
  inicial; a consistência interna síntese × tabela já é determinística).

---

## Instalação

Requer Python 3.10+.

```bash
# a partir da pasta verificador-contestacao/
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

## Demonstração rápida (um clique)

Para mostrar a ferramenta funcionando sem configurar nada à mão, use o script
`demo.ps1` (Windows/PowerShell). Ele cria o ambiente virtual se preciso,
instala as dependências e roda o verificador sobre a minuta de teste (PDF e
HTML):

```powershell
powershell -ExecutionPolicy Bypass -File .\demo.ps1
```

## Como rodar

```bash
# relatório legível no terminal
python -m src.verificador tests/fixtures/minuta_teste.pdf

# também funciona com o HTML nativo do SAPIENS
python -m src.verificador tests/fixtures/minuta_teste.html

# gravar o relatório JSON em arquivo
python -m src.verificador tests/fixtures/minuta_teste.pdf --json saida.json

# imprimir apenas o JSON no stdout
python -m src.verificador tests/fixtures/minuta_teste.pdf --so-json
```

O **código de saída** é `1` quando o veredito é `REPROVADO` e `0` quando
`APROVADO` — útil para automações/CI.

### Formato de saída

Cada verificação tem `{ id, bloco, descricao, status, mensagem, evidencia }`,
com `status ∈ {OK, ERRO, VERIFICAR, INFO}`. O **veredito** é `REPROVADO` se
houver qualquer `ERRO`; caso contrário `APROVADO`, listando os `VERIFICAR`
pendentes. Veja exemplos em [`examples/`](examples/).

## Testes

```bash
python -m pytest -q
```

Os testes (em `tests/`) confirmam, sobre a minuta de teste, que o script:
identifica o endereçamento como JEF; extrai NB/DER/processo/autor; detecta a
marcação amarela / instrução não removida (gerando `ERRO`); reporta as
preliminares presentes e a ausente (Prescrição); cataloga as teses; e não gera
falsos positivos nos itens corretos do gabarito.

---

## Estrutura do projeto

```
verificador-contestacao/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── utils.py             # normalização e busca de texto
│   ├── extractor.py         # extração de texto (PDF via pdfplumber, HTML via BeautifulSoup)
│   ├── segmenter.py         # segmentação em seções + objeto Minuta
│   ├── report.py            # Resultado/Relatorio + serialização JSON/terminal
│   ├── verificador.py       # orquestrador + CLI (entry point)
│   └── rules/
│       ├── __init__.py      # interface Regra + registry
│       ├── estrutural.py    # Bloco 1
│       ├── preliminares.py  # Bloco 2 (presença)
│       ├── redistribuicao.py# Bloco 6
│       ├── teses.py         # catalogação de teses (Blocos 3/4/5)
│       └── llm_stubs.py     # pontos de extensão da fase do LLM
├── tests/
│   ├── fixtures/            # minuta_teste.pdf / .html
│   └── test_*.py
└── examples/                # saídas de exemplo
```

## Princípios de design

- Cada regra é um objeto isolado que implementa a interface comum `Regra`
  (`verificar(minuta) -> list[Resultado]`), fácil de testar unitariamente.
- Um **registry** (`@registrar` em `src/rules/__init__.py`) coleta as regras —
  adicionar uma nova regra não exige mexer no orquestrador.
- A futura camada de **LLM** usa a **mesma interface** (`Regra`): os stubs em
  `llm_stubs.py` já a seguem.
- Sem rede, sem LLM, sem ML nesta fase. Código e comentários em português.
