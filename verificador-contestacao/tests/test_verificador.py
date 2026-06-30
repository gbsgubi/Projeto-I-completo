"""Testes de integração do orquestrador: veredito, teses e redistribuição."""

from src.report import Status


def _por_id(relatorio, prefixo):
    return [r for r in relatorio.resultados if r.id.startswith(prefixo)]


def test_veredito_reprovado(relatorio_pdf):
    # a marcação de edição não removida é um ERRO => REPROVADO
    assert relatorio_pdf.veredito == "REPROVADO"
    assert len(relatorio_pdf.erros) >= 1


def test_veredito_consistente_pdf_html(relatorio_pdf, relatorio_html):
    assert relatorio_pdf.veredito == relatorio_html.veredito == "REPROVADO"


def test_catalogo_teses_sem_codigos(relatorio_pdf):
    # a minuta de teste usa prosa, sem códigos CTN-/DIVESP-
    res = _por_id(relatorio_pdf, "345-catalogo-teses")[0]
    assert res.status == Status.INFO
    assert "Nenhuma tese" in res.mensagem


def test_redistribuicao_sem_flags(relatorio_pdf):
    # não há vigilante/saúde/professor no caso de teste -> tudo OK
    for prefixo in ("6.1-vigilante", "6.2-saude", "6.3-professor"):
        res = _por_id(relatorio_pdf, prefixo)[0]
        assert res.status == Status.OK, (prefixo, res.mensagem)


def test_sem_falsos_positivos_nos_itens_corretos(relatorio_pdf):
    # itens marcados como corretos no gabarito não devem virar ERRO:
    # endereçamento, campos, renúncia JEF, redistribuição.
    ids_corretos = (
        "1.1-enderecamento", "1.2-campos-obrigatorios", "2.3-renuncia-jef",
        "6.1-vigilante", "6.2-saude", "6.3-professor",
    )
    for r in relatorio_pdf.resultados:
        if any(r.id.startswith(p) for p in ids_corretos):
            assert r.status != Status.ERRO, (r.id, r.mensagem)


def test_json_serializavel(relatorio_pdf):
    import json
    dados = json.loads(relatorio_pdf.to_json())
    assert dados["veredito"] == "REPROVADO"
    assert "verificacoes" in dados
    assert len(dados["verificacoes"]) > 0
