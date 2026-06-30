"""Testes do Bloco 2 (presença de preliminares)."""

from src.report import Status


def _preliminar(relatorio, pid):
    for r in relatorio.resultados:
        if r.id == f"2.presenca:{pid}":
            return r
    raise AssertionError(f"preliminar {pid} não encontrada no relatório")


def test_preliminares_presentes(relatorio_pdf):
    for pid in ("juizo-digital", "conciliacao", "renuncia-60sm", "decadencia"):
        assert "PRESENTE" in _preliminar(relatorio_pdf, pid).mensagem, pid


def test_prescricao_ausente(relatorio_pdf):
    assert "AUSENTE" in _preliminar(relatorio_pdf, "prescricao").mensagem


def test_preliminares_presentes_html(relatorio_html):
    for pid in ("juizo-digital", "conciliacao", "renuncia-60sm", "decadencia"):
        assert "PRESENTE" in _preliminar(relatorio_html, pid).mensagem, pid
    assert "AUSENTE" in _preliminar(relatorio_html, "prescricao").mensagem


def test_renuncia_jef_ok(relatorio_pdf):
    res = [r for r in relatorio_pdf.resultados if r.id == "2.3-renuncia-jef"]
    assert len(res) == 1
    # JEF + renúncia presente => OK, não gera erro
    assert res[0].status == Status.OK
