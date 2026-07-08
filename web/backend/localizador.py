# -*- coding: utf-8 -*-
"""Localizador de evidências no PDF (Fase 2 — camada visual).

Recebe o texto de evidência produzido pelo verificador (Fase 1) e devolve as
coordenadas dos trechos correspondentes dentro do PDF, NORMALIZADAS (0.0–1.0)
em relação à largura/altura de cada página. A lógica de regras/veredito NÃO
mora aqui — este módulo apenas encontra "onde" a evidência está no documento.

Estratégia em três níveis (robustez > precisão milimétrica):
  1. ``page.search_for`` com o trecho completo (rápido; cobre o caso simples).
  2. O mesmo, após colapsar espaços/quebras de linha.
  3. Casamento de TOKENS normalizados (sem acento, caixa baixa, pontuação de
     borda removida) contra as palavras da página (``page.get_text("words")``),
     aceitando a maior corrida contígua ("âncora") — necessário porque as
     evidências da Fase 1 vêm com espaços colapsados e frequentemente cortadas
     no meio de uma palavra (ex.: "...esso nº 5013344-10...").

Se nada for encontrado, devolve lista vazia — NUNCA inventa posição.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import fitz  # PyMuPDF

# ---------------------------------------------------------------------------
# Pré-processamento da evidência (formato produzido pela Fase 1)
# ---------------------------------------------------------------------------

# prefixo usado pelas regras de marcação de edição (estrutural.py)
_PREFIXOS = ("instrução remanescente:", "instrucao remanescente:")

# aspas tipográficas -> retas (o texto do PDF usa retas após extração)
_TROCAS = {"“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-"}


def extrair_trechos(evidencia: str) -> list[str]:
    """Divide a evidência da Fase 1 em trechos "buscáveis" no PDF.

    Trata o formato composto (partes unidas por " | "), remove prefixos
    descritivos, aspas envolventes e as reticências de recorte ("...").
    """
    if not evidencia:
        return []
    trechos: list[str] = []
    for parte in evidencia.split(" | "):
        t = parte.strip()
        for de, para in _TROCAS.items():
            t = t.replace(de, para)
        baixo = t.lower()
        for prefixo in _PREFIXOS:
            if baixo.startswith(prefixo):
                t = t[len(prefixo):].strip()
                break
        t = t.strip('"').strip()
        # remove as reticências de recorte nas pontas
        t = re.sub(r"^\.{3}", "", t)
        t = re.sub(r"\.{3}$", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) >= 8 and t not in trechos:
            trechos.append(t)
    return trechos


# ---------------------------------------------------------------------------
# Normalização de tokens (nível 3)
# ---------------------------------------------------------------------------

_PONTUACAO_BORDA = "\"'()[]{}.,;:!?«»<>"


def _norm_token(palavra: str) -> str:
    """Token comparável: sem acentos, caixa baixa, pontuação de borda fora."""
    s = unicodedata.normalize("NFKD", palavra)
    s = s.encode("ascii", "ignore").decode("ascii")
    return s.casefold().strip(_PONTUACAO_BORDA)


def _tokens(texto: str) -> list[str]:
    return [t for t in (_norm_token(p) for p in texto.split()) if t]


@dataclass
class _PalavraPagina:
    """Palavra da página com posição (rect em pontos) e linha de origem."""

    token: str
    rect: fitz.Rect
    bloco: int
    linha: int


def _palavras_da_pagina(page: fitz.Page) -> list[_PalavraPagina]:
    palavras = []
    for x0, y0, x1, y1, palavra, bloco, linha, _ in page.get_text("words"):
        token = _norm_token(palavra)
        if token:
            palavras.append(_PalavraPagina(token, fitz.Rect(x0, y0, x1, y1), bloco, linha))
    return palavras


def _maior_corrida(evidencia: list[str], pagina: list[str]) -> tuple[int, int]:
    """Maior corrida contígua comum (posição na página, comprimento).

    Programação dinâmica clássica de "longest common substring" sobre listas
    de tokens; os textos são pequenos (evidência ~30 tokens, página ~600).
    """
    m, n = len(evidencia), len(pagina)
    melhor_len, melhor_fim = 0, -1
    anterior = [0] * (m + 1)
    for j in range(1, n + 1):
        atual = [0] * (m + 1)
        for i in range(1, m + 1):
            if evidencia[i - 1] == pagina[j - 1]:
                atual[i] = anterior[i - 1] + 1
                if atual[i] > melhor_len:
                    melhor_len, melhor_fim = atual[i], j
        anterior = atual
    return melhor_fim - melhor_len, melhor_len  # (início na página, tamanho)


def _agrupar_por_linha(palavras: list[_PalavraPagina]) -> list[fitz.Rect]:
    """Une os retângulos das palavras casadas, um retângulo por linha."""
    grupos: dict[tuple[int, int], fitz.Rect] = {}
    for p in palavras:
        chave = (p.bloco, p.linha)
        if chave in grupos:
            grupos[chave] |= p.rect  # união de retângulos
        else:
            grupos[chave] = fitz.Rect(p.rect)
    return list(grupos.values())


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

# proporção mínima da evidência que a âncora precisa cobrir para valer
_MIN_TOKENS_ANCORA = 3
_MIN_FRACAO_ANCORA = 0.35


def _rect_normalizado(rect: fitz.Rect, page: fitz.Page) -> list[float]:
    w, h = page.rect.width, page.rect.height
    return [
        round(rect.x0 / w, 4),
        round(rect.y0 / h, 4),
        round(rect.x1 / w, 4),
        round(rect.y1 / h, 4),
    ]


def _localizar_trecho(doc: fitz.Document, trecho: str) -> list[dict]:
    # níveis 1 e 2: search_for direto (o trecho já chega com espaços colapsados)
    achados: list[dict] = []
    for numero, page in enumerate(doc, start=1):
        if page.rotation:  # PDF do SAPIENS não roda páginas; apenas registrar
            print(f"[localizador] aviso: página {numero} com rotação {page.rotation}°")
        for rect in page.search_for(trecho):
            achados.append({"pagina": numero, "rect": _rect_normalizado(rect, page)})
    if achados:
        return achados

    # nível 3: maior âncora por casamento de tokens
    tokens_ev = _tokens(trecho)
    if not tokens_ev:
        return []
    minimo = min(len(tokens_ev),
                 max(_MIN_TOKENS_ANCORA, int(len(tokens_ev) * _MIN_FRACAO_ANCORA)))

    melhor: tuple[int, int, int, list[_PalavraPagina]] | None = None  # (len, pág, iní, palavras)
    for numero, page in enumerate(doc, start=1):
        palavras = _palavras_da_pagina(page)
        inicio, tamanho = _maior_corrida(tokens_ev, [p.token for p in palavras])
        if tamanho >= minimo and (melhor is None or tamanho > melhor[0]):
            melhor = (tamanho, numero, inicio, palavras)

    if melhor is None:
        return []
    tamanho, numero, inicio, palavras = melhor
    page = doc[numero - 1]
    casadas = palavras[inicio:inicio + tamanho]
    return [
        {"pagina": numero, "rect": _rect_normalizado(rect, page)}
        for rect in _agrupar_por_linha(casadas)
    ]


def localizar(pdf_path: str, texto_evidencia: str) -> list[dict]:
    """Localiza a evidência no PDF.

    Retorna ``[{"pagina": int (1-based), "rect": [x0, y0, x1, y1]}, ...]`` com
    coordenadas normalizadas (0.0–1.0). Lista vazia se nada for encontrado.
    """
    trechos = extrair_trechos(texto_evidencia)
    if not trechos:
        return []
    with fitz.open(pdf_path) as doc:
        destaques: list[dict] = []
        vistos: set[tuple] = set()
        for trecho in trechos:
            for d in _localizar_trecho(doc, trecho):
                chave = (d["pagina"], tuple(d["rect"]))
                if chave not in vistos:
                    vistos.add(chave)
                    destaques.append(d)
        return destaques


def dimensoes(pdf_path: str) -> list[dict]:
    """Dimensões de cada página em pontos: [{numero, largura, altura}, ...]."""
    with fitz.open(pdf_path) as doc:
        return [
            {
                "numero": i + 1,
                "largura": round(page.rect.width, 2),
                "altura": round(page.rect.height, 2),
            }
            for i, page in enumerate(doc)
        ]
