"""Testes da extração de texto (PDF e HTML)."""

from src.extractor import extrair
from src.utils import normalizar


def test_extrai_texto_pdf(caminho_pdf):
    doc = extrair(caminho_pdf)
    assert doc.formato == "pdf"
    # no PDF o título pode quebrar em duas linhas ("JUIZADO ESPECIAL\nFEDERAL");
    # a verificação real usa texto normalizado (espaços colapsados, sem acento).
    assert "juizado especial federal" in normalizar(doc.texto)
    assert "joao da silva santos" in normalizar(doc.texto)
    # no PDF o destaque amarelo não é detectável estruturalmente
    assert doc.suporta_amarelo is False
    assert doc.destaques_amarelos == []


def test_extrai_texto_html(caminho_html):
    doc = extrair(caminho_html)
    assert doc.formato == "html"
    assert "JUIZADO ESPECIAL FEDERAL" in doc.texto
    # o HTML permite detectar o destaque amarelo diretamente
    assert doc.suporta_amarelo is True
    assert any("VERIFICAR" in d for d in doc.destaques_amarelos)


def test_formato_invalido(tmp_path):
    arq = tmp_path / "x.txt"
    arq.write_text("nada")
    try:
        extrair(str(arq))
        assert False, "deveria ter levantado ValueError"
    except ValueError:
        pass
