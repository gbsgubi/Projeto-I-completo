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

Apenas verificações de **presença/ausência** e de **padrão textual**:

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

### Bloco 2 — Preliminares (somente PRESENÇA)
- Detecta se cada preliminar está **PRESENTE** ou **AUSENTE** (Juízo 100%
  Digital, Audiência de Conciliação, Renúncia aos 60 SM, Decadência, Prescrição,
  Coisa Julgada, Litispendência, PPP não apresentado, Períodos reconhecidos
  administrativamente, Petição inicial inepta). **Não** decide ainda se a
  preliminar *deveria* estar presente (isso é da fase do LLM).
- **Exceção determinística**: endereçamento JEF + Renúncia aos 60 SM ausente →
  `ERRO` (correlação puramente estrutural).

### Bloco 6 — Redistribuição (sugestão, nunca erro)
- **VIGILANTE**: vigilante, vigia, guarda, policial.
- **SAÚDE**: profissional/ambiente de saúde + menção a agente biológico.
- **PROFESSOR**: professor com indício de período posterior a 1981.

### Teses presentes (Blocos 3/4/5 — somente CATALOGAÇÃO)
- Lista as teses padronizadas presentes (nomes começando por `CTN-`,
  `DIVESP-NOTA-`, etc.). **Não** avalia compatibilidade com agente/período.

---

## O que ficou para a fase do LLM (pontos de extensão)

Estão documentados como stubs em [`src/rules/llm_stubs.py`](src/rules/llm_stubs.py),
seguindo a **mesma interface `Regra`** — basta implementá-los e registrá-los:

- **Compatibilidade tese × agente × período** (marcos temporais de ruído,
  calor, etc.). → corresponde ao **Erro 2** do gabarito.
- **Distinção entre as três situações de PPP não apresentado.**
- **Decadência/prescrição condicionadas a datas e tipo de ação** (concessão x
  revisão). → corresponde aos **Erros 4 e 5** do gabarito.
- **Cobertura dos períodos requeridos na petição inicial** (exige ler a inicial,
  que não está na minuta).

> Por isso, nesta fase o script **não** detecta o Erro 2 (tese de ruído na
> fronteira de 03/12/1998) nem o Erro 5 (decadência em ação de concessão): ambos
> dependem da camada de LLM.

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
