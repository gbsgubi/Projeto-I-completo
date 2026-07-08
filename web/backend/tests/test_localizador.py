# -*- coding: utf-8 -*-
"""Testes do localizador de evidências (Fase 2)."""

import sys
from pathlib import Path

import fitz
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from localizador import dimensoes, extrair_trechos, localizar  # noqa: E402

RAIZ_PROJETO = Path(__file__).resolve().parents[3]
PDF_REAL = RAIZ_PROJETO / "contestacao_05.pdf"


@pytest.fixture()
def pdf_sintetico(tmp_path: Path) -> str:
    """PDF de duas páginas com texto conhecido, gerado na hora."""
    doc = fitz.open()
    pagina1 = doc.new_page()  # A4 por padrão (595 x 842 pt)
    pagina1.insert_text(
        (72, 100),
        "Trata-se de ação em que pleiteia a parte autora a concessão do",
    )
    pagina1.insert_text(
        (72, 120),
        "benefício de aposentadoria especial, com exposição ao ruído de",
    )
    pagina1.insert_text((72, 140), "90 dB(A) no período de 2005 a 2010.")
    pagina2 = doc.new_page()
    pagina2.insert_text(
        (72, 100),
        "[VERIFICAR: deixar a preliminar de decadência somente quando",
    )
    pagina2.insert_text((72, 120), "contabilizar 10 anos do ajuizamento]")
    caminho = tmp_path / "sintetico.pdf"
    doc.save(caminho)
    doc.close()
    return str(caminho)


# ---------------------------------------------------------------------------
# extrair_trechos — formato da evidência da Fase 1
# ---------------------------------------------------------------------------

def test_extrair_trechos_simples():
    assert extrair_trechos("...exposição ao ruído de 90 dB(A)...") == [
        "exposição ao ruído de 90 dB(A)"
    ]


def test_extrair_trechos_composto_com_prefixo():
    evidencia = (
        'instrução remanescente: "...deixar a preliminar de decadência some..." | '
        'instrução remanescente: "...decadência somente quando contabiliz..."'
    )
    trechos = extrair_trechos(evidencia)
    assert len(trechos) == 2
    assert trechos[0] == "deixar a preliminar de decadência some"


def test_extrair_trechos_vazio():
    assert extrair_trechos("") == []
    assert extrair_trechos(None) == []


# ---------------------------------------------------------------------------
# localizar — evidência ENCONTRADA
# ---------------------------------------------------------------------------

def test_localiza_trecho_exato(pdf_sintetico):
    destaques = localizar(pdf_sintetico, "ruído de 90 dB(A)")
    assert destaques, "deveria encontrar o trecho exato"
    assert destaques[0]["pagina"] == 1
    for d in destaques:
        x0, y0, x1, y1 = d["rect"]
        assert 0.0 <= x0 < x1 <= 1.0
        assert 0.0 <= y0 < y1 <= 1.0


def test_localiza_evidencia_recortada_no_meio_de_palavra(pdf_sintetico):
    """Formato real da Fase 1: recorte com '...' cortando palavras nas pontas."""
    evidencia = "...osição ao ruído de 90 dB(A) no período de 2005 a 20..."
    destaques = localizar(pdf_sintetico, evidencia)
    assert destaques, "a âncora de tokens deveria encontrar o miolo do trecho"
    assert destaques[0]["pagina"] == 1


def test_localiza_na_segunda_pagina(pdf_sintetico):
    destaques = localizar(pdf_sintetico, "deixar a preliminar de decadência")
    assert destaques
    assert all(d["pagina"] == 2 for d in destaques)


def test_localiza_ignorando_caixa(pdf_sintetico):
    destaques = localizar(pdf_sintetico, "RUÍDO DE 90 DB(A) NO PERÍODO")
    assert destaques


# ---------------------------------------------------------------------------
# localizar — evidência INEXISTENTE (nunca inventar posição)
# ---------------------------------------------------------------------------

def test_nao_encontra_evidencia_inexistente(pdf_sintetico):
    destaques = localizar(
        pdf_sintetico, "agente químico benzeno acima do limite de tolerância"
    )
    assert destaques == []


def test_evidencia_vazia(pdf_sintetico):
    assert localizar(pdf_sintetico, "") == []


# ---------------------------------------------------------------------------
# dimensoes
# ---------------------------------------------------------------------------

def test_dimensoes(pdf_sintetico):
    dims = dimensoes(pdf_sintetico)
    assert [d["numero"] for d in dims] == [1, 2]
    assert dims[0]["largura"] == pytest.approx(595, abs=1)
    assert dims[0]["altura"] == pytest.approx(842, abs=1)


# ---------------------------------------------------------------------------
# integração com uma peça real do banco de testes
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not PDF_REAL.exists(), reason="contestacao_05.pdf não está no repo")
def test_integracao_contestacao_05():
    """Evidência real emitida pela Fase 1 para a contestação 05."""
    evidencia = (
        'instrução remanescente: "...r o ato de concessão de seu benefício. '
        '[VERIFICAR: deixar a preliminar de decadência some..."'
    )
    destaques = localizar(str(PDF_REAL), evidencia)
    assert destaques, "deveria localizar a anotação não removida na peça real"
    for d in destaques:
        x0, y0, x1, y1 = d["rect"]
        assert 0.0 <= x0 < x1 <= 1.0
        assert 0.0 <= y0 < y1 <= 1.0
