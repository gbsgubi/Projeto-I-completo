"""Extração de texto e tabelas a partir de PDF e HTML.

- PDF (formato principal): usa ``pdfplumber`` para extrair o texto.
- HTML (formato secundário, nativo do SAPIENS): usa ``BeautifulSoup``. O HTML
  preserva a estrutura semântica e permite detectar diretamente os destaques
  em amarelo (classe CSS ``amarelo`` ou ``style`` com fundo amarelo).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field


@dataclass
class DocumentoExtraido:
    """Resultado bruto da extração, antes da segmentação.

    Campos:
      - caminho: caminho do arquivo de origem.
      - formato: "pdf" ou "html".
      - texto: texto plano extraído.
      - destaques_amarelos: trechos marcados em amarelo (apenas HTML).
      - suporta_amarelo: True se o formato permite detectar amarelo (HTML).
        No PDF o destaque vira texto comum, então a detecção é só textual.
    """

    caminho: str
    formato: str
    texto: str
    destaques_amarelos: list[str] = field(default_factory=list)
    suporta_amarelo: bool = False


def extrair(caminho: str) -> DocumentoExtraido:
    """Detecta o formato pela extensão e despacha para o extrator adequado."""
    ext = os.path.splitext(caminho)[1].lower()
    if ext == ".pdf":
        return _extrair_pdf(caminho)
    if ext in (".html", ".htm"):
        return _extrair_html(caminho)
    raise ValueError(
        f"Formato não suportado: '{ext}'. Use .pdf, .html ou .htm."
    )


def _extrair_pdf(caminho: str) -> DocumentoExtraido:
    import pdfplumber

    paginas: list[str] = []
    with pdfplumber.open(caminho) as pdf:
        for pagina in pdf.pages:
            txt = pagina.extract_text() or ""
            paginas.append(txt)
    texto = "\n".join(paginas)
    return DocumentoExtraido(
        caminho=caminho,
        formato="pdf",
        texto=texto,
        destaques_amarelos=[],
        suporta_amarelo=False,
    )


# cores consideradas "amarelas" em background (heurística)
_RE_AMARELO_STYLE = re.compile(
    r"background[^;:]*:\s*"
    r"(#f{0,1}f{1,2}[0e]{0,1}[0-9a-f]{0,3}"  # variações de #ff0/#ffff00/#fff200
    r"|#fff200|#ffff00|#ff0|yellow|rgb\(\s*255\s*,\s*2[0-9][0-9]\s*,\s*0)",
    re.IGNORECASE,
)


def _eh_amarelo(tag) -> bool:
    """True se a tag tem classe 'amarelo' ou style com fundo amarelo."""
    classes = tag.get("class") or []
    if any("amarelo" in c.lower() for c in classes):
        return True
    style = tag.get("style") or ""
    if _RE_AMARELO_STYLE.search(style):
        return True
    return False


def _extrair_html(caminho: str) -> DocumentoExtraido:
    from bs4 import BeautifulSoup

    with open(caminho, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # remover folha de estilo/scripts do texto plano
    for t in soup(["style", "script"]):
        t.decompose()

    destaques: list[str] = []
    for tag in soup.find_all(True):
        if _eh_amarelo(tag):
            txt = tag.get_text(separator=" ", strip=True)
            if txt:
                destaques.append(re.sub(r"\s+", " ", txt))

    texto = soup.get_text(separator="\n")
    # normaliza linhas em branco excessivas
    texto = re.sub(r"\n[ \t]*\n+", "\n", texto)
    texto = "\n".join(linha.strip() for linha in texto.splitlines())

    return DocumentoExtraido(
        caminho=caminho,
        formato="html",
        texto=texto,
        destaques_amarelos=destaques,
        suporta_amarelo=True,
    )
