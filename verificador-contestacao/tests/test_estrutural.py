"""Testes do Bloco 1 (estrutural) e do veredito final."""

from src.report import Status


def _por_id(relatorio, prefixo):
    return [r for r in relatorio.resultados if r.id.startswith(prefixo)]


# ---- 1.1 Endereçamento -----------------------------------------------------

def test_enderecamento_jef_pdf(relatorio_pdf):
    res = _por_id(relatorio_pdf, "1.1-enderecamento")
    assert len(res) == 1
    assert res[0].status == Status.INFO
    assert "JEF" in res[0].mensagem


def test_enderecamento_jef_html(relatorio_html):
    res = _por_id(relatorio_html, "1.1-enderecamento")
    assert "JEF" in res[0].mensagem


# ---- 1.2 Campos obrigatórios -----------------------------------------------

def test_campos_obrigatorios_presentes(relatorio_pdf):
    campos = _por_id(relatorio_pdf, "1.2-campos-obrigatorios")
    # NB, DER, processo, autor, benefício -> 5 campos
    assert len(campos) == 5
    # todos devem estar presentes (OK) na minuta de teste
    assert all(c.status == Status.OK for c in campos), [
        (c.descricao, c.status) for c in campos
    ]


def test_extrai_nb_der_processo_autor(relatorio_pdf):
    campos = {c.descricao: c for c in _por_id(relatorio_pdf, "1.2-campos-obrigatorios")}
    assert campos["Campo obrigatório: NB"].status == Status.OK
    assert campos["Campo obrigatório: DER"].status == Status.OK
    assert campos["Campo obrigatório: Número do processo"].status == Status.OK
    assert campos["Campo obrigatório: Nome do autor"].status == Status.OK


# ---- 1.3 Marcações de edição não removidas ---------------------------------

def test_marcacao_amarela_gera_erro_html(relatorio_html):
    res = _por_id(relatorio_html, "1.3-marcacoes-edicao")[0]
    assert res.status == Status.ERRO
    assert "amarelo" in (res.evidencia or "").lower()


def test_instrucao_nao_removida_gera_erro_pdf(relatorio_pdf):
    # no PDF a detecção é textual (colchetes / "VERIFICAR" / "deixar a preliminar")
    res = _por_id(relatorio_pdf, "1.3-marcacoes-edicao")[0]
    assert res.status == Status.ERRO


def test_assinatura_nao_e_falso_positivo(relatorio_pdf):
    # a linha de assinatura (só underscores) não deve contar como placeholder;
    # o ERRO deve vir da instrução/colchetes, não do sublinhado de assinatura.
    res = _por_id(relatorio_pdf, "1.3-marcacoes-edicao")[0]
    assert "assinatura" not in (res.evidencia or "").lower()
