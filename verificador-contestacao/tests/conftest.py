"""Configuração e fixtures compartilhadas dos testes."""

import os
import sys

import pytest

# garante que o pacote 'src' seja importável a partir da raiz do projeto
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def caminho_pdf():
    return os.path.join(FIXTURES, "minuta_teste.pdf")


@pytest.fixture
def caminho_html():
    return os.path.join(FIXTURES, "minuta_teste.html")


@pytest.fixture
def relatorio_pdf(caminho_pdf):
    from src.verificador import verificar_minuta
    return verificar_minuta(caminho_pdf)


@pytest.fixture
def relatorio_html(caminho_html):
    from src.verificador import verificar_minuta
    return verificar_minuta(caminho_html)
