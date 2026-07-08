# Verificador de Contestação — App de demonstração (Fase 2)

Interface visual por cima do verificador determinístico da **Fase 1**
(`verificador-contestacao/`): o estagiário sobe uma minuta (**PDF** ou HTML),
o app roda o verificador existente e mostra o diagnóstico — **com os erros
grifados no lugar exato onde ocorrem dentro do PDF**.

> **Princípio nº 1:** este app **não reimplementa nenhuma regra**. O veredito e
> todos os resultados vêm de `src.verificador.verificar_minuta` (Fase 1),
> importado diretamente. A Fase 2 só adiciona: a camada web (FastAPI), a
> localização de evidências no PDF (`localizador.py`, PyMuPDF) e a interface
> (React + PDF.js).

Roda **100% offline em localhost** — sem CDN, sem fontes remotas, sem
telemetria. O PDF nunca sai da máquina.

---

## Como rodar (um comando)

Pré-requisitos: Python 3.12+ e Node.js 18+ (usados apenas para instalar/buildar).

```powershell
cd web
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

O script cria o venv, instala as dependências, builda o frontend (só na
primeira vez) e abre `http://localhost:8000` no navegador.
Opções: `-Porta 8080` muda a porta; `-Rebuild` refaz deps + build.

### Modo desenvolvimento (opcional)

```powershell
# terminal 1 — backend
cd web\backend
..\.venv\Scripts\python.exe -m uvicorn app:app --port 8000 --reload

# terminal 2 — frontend com hot-reload (proxy /api -> 8000)
cd web\frontend
npm run dev
```

### Testes

```powershell
cd web
.\.venv\Scripts\python.exe -m pytest backend\tests\ -v
```

---

## O que a interface faz

- **Tela inicial:** upload por arrastar/soltar (`.pdf`/`.html`) + **galeria** com
  as 15 peças do banco de testes (`contestacao_03.pdf … 17.pdf`), mostrando o
  veredito **esperado** (gabarito) × **obtido** (verificador), com indicador de
  acerto. Com a camada determinística completa, todas as peças devem bater ✓
  com o gabarito — uma divergência ✘ indica regressão nas regras.
- **Tela de diagnóstico** (duas colunas; empilha no mobile):
  - *Esquerda* — o PDF renderizado (PDF.js) com **overlays translúcidos** sobre
    cada evidência localizada: vermelho = `ERRO`, âmbar = `VERIFICAR`,
    azul = alerta de redistribuição (`INFO` do Bloco 6). Cada grifo tem um
    rótulo com o id da regra (ex.: `1.3-marcacoes-edicao`).
  - *Direita* — banner de veredito (APROVADO/REPROVADO) com contadores,
    filtro "Todos / Só ERRO" e a lista de verificações **agrupada pelos blocos
    do verificador**, cada item com badge de status, mensagem e evidência.
  - **Clicar** num item localizável rola o PDF até o grifo e o faz pulsar;
    **hover** num grifo destaca o item do painel (e vice-versa).
  - Erros de **ausência** (ex.: NB faltando) não têm posição no documento:
    aparecem no painel com a nota "sem posição no documento" — nunca com um
    grifo inventado.

## Arquitetura

```
web/
├── run.ps1                # sobe tudo com um comando
├── backend/
│   ├── app.py             # FastAPI: /api/verificar, /api/minuta/{id},
│   │                      #          /api/exemplos, frontend estático
│   ├── localizador.py     # evidência -> coordenadas normalizadas (PyMuPDF)
│   ├── requirements.txt
│   └── tests/test_localizador.py
└── frontend/              # React + Vite + Tailwind + pdfjs-dist (empacotado)
    └── src/
        ├── App.jsx, api.js, constantes.js, estilos.css
        └── componentes/
            ├── TelaInicial.jsx     # upload + galeria
            ├── Galeria.jsx         # esperado × obtido (gabarito)
            ├── Diagnostico.jsx     # layout 2 colunas + sync hover/click
            ├── VisualizadorPdf.jsx # canvas PDF.js + overlays em %
            └── PainelDiagnostico.jsx
```

### Como o grifo funciona

1. O backend roda a Fase 1 e, para cada resultado com evidência textual
   (`ERRO`, `VERIFICAR` e os alertas de redistribuição), chama
   `localizador.localizar(pdf, evidencia)`.
2. O localizador tenta, nesta ordem: `page.search_for` com o trecho completo →
   busca com espaços colapsados → **casamento de tokens normalizados** contra
   `page.get_text("words")`, aceitando a maior âncora contígua (necessário
   porque as evidências da Fase 1 chegam recortadas no meio de palavras).
3. As coordenadas voltam **normalizadas (0–1)** pela largura/altura da página;
   o frontend posiciona os overlays em **porcentagem**, então nenhum
   descasamento de escala com o PDF.js é possível.
4. Evidência não encontrada → lista vazia → item "sem posição no documento".

### Contrato de `/api/verificar` (resumo)

```json
{
  "minuta_id": "…", "tipo": "pdf",
  "veredito": "REPROVADO",
  "resumo": { "erro": 1, "verificar": 0, "ok": 9, "info": 12 },
  "paginas": [ { "numero": 1, "largura": 595, "altura": 842 } ],
  "resultados": [ {
      "regra_id": "1.3-marcacoes-edicao",
      "bloco": "Bloco 1 - Estrutural",
      "descricao": "…", "status": "ERRO", "mensagem": "…", "evidencia": "…",
      "localizavel": true,
      "destaques": [ { "pagina": 1, "rect": [0.70, 0.71, 0.88, 0.73] } ]
  } ]
}
```

Obs.: `bloco` é a string emitida pelo verificador (ex.: `"Bloco 1 -
Estrutural"`), não um inteiro — nada é recalculado sobre a saída da Fase 1.

## Dependências adicionadas nesta fase

| Onde | Pacote | Para quê |
|------|--------|----------|
| backend | `fastapi`, `uvicorn`, `python-multipart` | API + upload + servidor |
| backend | `PyMuPDF` (`fitz`) | localizar evidências no PDF |
| frontend | `react`, `react-dom`, `vite`, `@vitejs/plugin-react` | interface |
| frontend | `pdfjs-dist` | renderizar o PDF no navegador (worker empacotado) |
| frontend | `tailwindcss`, `@tailwindcss/vite` | estilos |

(`pdfplumber`, `beautifulsoup4` e `pytest` já eram da Fase 1 — o backend as
instala porque importa o verificador.)

## Limitações conhecidas

- Minutas **HTML** recebem o diagnóstico completo, mas sem visualização
  grifada (o viewer é de PDF).
- O grifo depende de a evidência da Fase 1 existir no texto do PDF; quando o
  texto não é localizável (regras de ausência), o item aparece só no painel.
- Uploads ficam numa pasta temporária do processo e morrem com o servidor.
