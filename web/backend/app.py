# -*- coding: utf-8 -*-
"""Backend FastAPI do app de demonstração (Fase 2).

Camada fina sobre o verificador existente (Fase 1):
  - recebe o upload da minuta;
  - invoca ``src.verificador.verificar_minuta`` (import direto — NENHUMA regra
    é reimplementada; veredito e resultados vêm 100% da Fase 1);
  - para resultados com evidência textual, chama o ``localizador`` (PyMuPDF)
    para obter as coordenadas normalizadas no PDF;
  - devolve o contrato de dados consumido pelo frontend;
  - serve o frontend buildado (React/Vite) como estático.

Roda 100% em localhost, sem nenhuma chamada externa.
"""

from __future__ import annotations

import re
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import localizador

# ---------------------------------------------------------------------------
# Integração com o verificador da Fase 1 (import direto, sem tocar nas regras)
# ---------------------------------------------------------------------------

RAIZ_PROJETO = Path(__file__).resolve().parents[2]
PACOTE_VERIFICADOR = RAIZ_PROJETO / "verificador-contestacao"

import sys  # noqa: E402

sys.path.insert(0, str(PACOTE_VERIFICADOR))

from src.verificador import verificar_minuta  # noqa: E402

# ---------------------------------------------------------------------------
# Estado do app (uploads temporários + exemplos do repositório)
# ---------------------------------------------------------------------------

PASTA_UPLOADS = Path(tempfile.mkdtemp(prefix="verificador-web-"))
MINUTAS: dict[str, Path] = {}  # id -> caminho do arquivo original

GABARITO_MD = RAIZ_PROJETO / "gabarito_contestacoes_03-16.md"
EXTENSOES_ACEITAS = {".pdf", ".html"}

app = FastAPI(title="Verificador de Contestação — demo (Fase 2)")

# CORS liberado apenas para o dev server do Vite (localhost); em produção o
# frontend é servido pelo próprio FastAPI e o CORS nem é exercitado.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Montagem da resposta (contrato de dados)
# ---------------------------------------------------------------------------

def _deve_localizar(status: str, mensagem: str) -> bool:
    """Quais resultados ganham grifo no PDF.

    ERRO e VERIFICAR, conforme o contrato; e também os INFO de redistribuição
    sugerida (flags do Bloco 6), que carregam evidência acionável.
    """
    if status in ("ERRO", "VERIFICAR"):
        return True
    return status == "INFO" and mensagem.startswith("Redistribuição sugerida")


def _executar_verificacao(caminho: Path, minuta_id: str) -> dict:
    """Roda a Fase 1 e monta o contrato de dados com os destaques."""
    relatorio = verificar_minuta(str(caminho))
    dados = relatorio.to_dict()  # veredito/resultados: fonte única = Fase 1

    eh_pdf = caminho.suffix.lower() == ".pdf"
    paginas = localizador.dimensoes(str(caminho)) if eh_pdf else []

    resumo = {"erro": 0, "verificar": 0, "ok": 0, "info": 0}
    resultados = []
    for v in dados["verificacoes"]:
        status = v["status"]
        resumo[status.lower()] += 1

        evidencia = v["evidencia"] or ""
        destaques: list[dict] = []
        if eh_pdf and evidencia and _deve_localizar(status, v["mensagem"]):
            destaques = localizador.localizar(str(caminho), evidencia)

        resultados.append({
            "regra_id": v["id"],
            "bloco": v["bloco"],
            "descricao": v["descricao"],
            "status": status,
            "mensagem": v["mensagem"],
            "evidencia": evidencia,
            "localizavel": bool(destaques),
            "destaques": destaques,
        })

    return {
        "minuta_id": minuta_id,
        "tipo": "pdf" if eh_pdf else "html",
        "veredito": dados["veredito"],
        "resumo": resumo,
        "paginas": paginas,
        "resultados": resultados,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/verificar")
async def api_verificar(arquivo: UploadFile) -> dict:
    sufixo = Path(arquivo.filename or "").suffix.lower()
    if sufixo not in EXTENSOES_ACEITAS:
        raise HTTPException(400, "Envie uma minuta .pdf ou .html")

    minuta_id = uuid.uuid4().hex
    destino = PASTA_UPLOADS / f"{minuta_id}{sufixo}"
    destino.write_bytes(await arquivo.read())
    MINUTAS[minuta_id] = destino

    try:
        return _executar_verificacao(destino, minuta_id)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(422, f"Não foi possível processar a minuta: {e}")


@app.get("/api/minuta/{minuta_id}")
def api_minuta(minuta_id: str) -> FileResponse:
    caminho = MINUTAS.get(minuta_id)
    if not caminho or not caminho.exists():
        raise HTTPException(404, "Minuta não encontrada (verifique novamente).")
    tipo = "application/pdf" if caminho.suffix == ".pdf" else "text/html"
    return FileResponse(caminho, media_type=tipo)


# ---- galeria de exemplos ---------------------------------------------------

def _gabarito() -> dict[str, dict]:
    """Lê o gabarito das peças 03–16: {"03": {"esperado": "APROVAR", "motivo": ...}}."""
    if not GABARITO_MD.exists():
        return {}
    gabarito = {}
    padrao = re.compile(r"^\|\s*(\d{2})\s*\|\s*(APROVAR|REPROVAR)\s*\|\s*(.+?)\s*\|\s*$")
    for linha in GABARITO_MD.read_text(encoding="utf-8").splitlines():
        m = padrao.match(linha)
        if m:
            numero, veredito, motivo = m.groups()
            motivo = motivo.strip().lstrip("—").strip()
            gabarito[numero] = {"esperado": veredito, "motivo": motivo or None}
    return gabarito


@app.get("/api/exemplos")
def api_exemplos() -> list[dict]:
    gabarito = _gabarito()
    exemplos = []
    for pdf in sorted(RAIZ_PROJETO.glob("contestacao_*.pdf")):
        numero = pdf.stem.split("_")[-1]
        info = gabarito.get(numero, {})
        exemplos.append({
            "numero": numero,
            "arquivo": pdf.name,
            "esperado": info.get("esperado"),
            "motivo": info.get("motivo"),
        })
    return exemplos


@app.post("/api/exemplos/{numero}/verificar")
def api_verificar_exemplo(numero: str) -> dict:
    caminho = RAIZ_PROJETO / f"contestacao_{numero}.pdf"
    if not caminho.exists():
        raise HTTPException(404, f"Exemplo contestacao_{numero}.pdf não existe.")
    minuta_id = f"exemplo-{numero}"
    MINUTAS[minuta_id] = caminho
    return _executar_verificacao(caminho, minuta_id)


# ---------------------------------------------------------------------------
# Frontend buildado (React/Vite) servido como estático
# ---------------------------------------------------------------------------

PASTA_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if PASTA_DIST.exists():
    app.mount("/", StaticFiles(directory=PASTA_DIST, html=True), name="frontend")
