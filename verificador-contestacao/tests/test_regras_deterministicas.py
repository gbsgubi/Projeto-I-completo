"""Testes das regras determinísticas adicionadas à Fase 1.

Cada teste monta uma minuta sintética mínima (texto plano) e verifica o
comportamento da regra isolada: ERRO quando o erro é certo, VERIFICAR quando
o período cruza um marco temporal (certeza impossível sem LLM) e OK/ausência
de falso positivo nos casos corretos.
"""

from src.extractor import DocumentoExtraido
from src.report import Status
from src.rules.agentes import (
    CalorLimiarPorPeriodo,
    ConsistenciaSinteseTabela,
    RuidoLimiarPorPeriodo,
    RuidoMetodologiaPorPeriodo,
    VedacaoConversaoPos2019,
    VicioCreaCrm,
)
from src.rules.indeferimento import IndeferimentoForcado
from src.rules.preliminares import (
    DecadenciaImpossivelPorDatas,
    PreliminaresSempreObrigatorias,
    RenunciaObrigatoriaNoJEF,
)
from src.rules.redistribuicao import SemPedidoTempoEspecial
from src.segmenter import segmentar


def _minuta(texto: str):
    doc = DocumentoExtraido(caminho="teste.txt", formato="pdf", texto=texto)
    return segmentar(doc)


_CABECALHO_JEF = (
    "JUIZ(A) FEDERAL DO JUIZADO ESPECIAL FEDERAL DA SUBSEÇÃO JUDICIÁRIA\n"
    "Processo nº 5018899-65.2025.4.03.6183\nDER: 20/06/2024\n"
)


def _bloco_ruido(periodo: str, teses: str) -> str:
    ini, fim = periodo.split(" a ")
    return (
        "III - DO MÉRITO\n"
        f"III.1 - Período de {ini} a {fim} - Agente: Ruído\n"
        f"Período(s): {ini} a {fim}\n"
        f"Agentes Nocivos:\n{teses}\n"
    )


# ---- 2.1/2.2 preliminares sempre obrigatórias ------------------------------

def test_juizo_digital_ausente_gera_erro():
    m = _minuta(_CABECALHO_JEF + "II.1 - Da Audiência de Conciliação\n...")
    res = {r.id: r for r in PreliminaresSempreObrigatorias().verificar(m)}
    assert res["2.1-juizo-digital-obrigatoria"].status == Status.ERRO
    assert res["2.2-conciliacao-obrigatoria"].status == Status.OK


def test_preliminares_obrigatorias_presentes_ok():
    m = _minuta(
        _CABECALHO_JEF
        + "II.1 - Do Juízo 100% Digital\n...\nII.2 - Da Audiência de Conciliação\n..."
    )
    res = PreliminaresSempreObrigatorias().verificar(m)
    assert all(r.status == Status.OK for r in res)


# ---- 2.3 renúncia 60 SM bidirecional ---------------------------------------

def test_renuncia_presente_na_jf_comum_gera_erro():
    m = _minuta(
        "JUIZ(A) FEDERAL DA 3ª VARA FEDERAL DA SUBSEÇÃO JUDICIÁRIA\n"
        "II.3 - Da Renúncia ao Valor Excedente a 60 Salários-Mínimos\n"
        "renuncie expressamente ao montante que ultrapasse sessenta salários\n"
    )
    (res,) = RenunciaObrigatoriaNoJEF().verificar(m)
    assert res.status == Status.ERRO
    assert "Justiça Federal comum" in res.mensagem


def test_renuncia_ausente_na_jf_comum_ok():
    m = _minuta("JUIZ(A) FEDERAL DA 3ª VARA FEDERAL DA SUBSEÇÃO JUDICIÁRIA\n...")
    (res,) = RenunciaObrigatoriaNoJEF().verificar(m)
    assert res.status == Status.OK


# ---- 2.4 decadência por datas ----------------------------------------------

def test_decadencia_com_prazo_impossivel_gera_erro():
    m = _minuta(_CABECALHO_JEF + "II.4 - Da Decadência\ndecaiu o direito...\n")
    (res,) = DecadenciaImpossivelPorDatas().verificar(m)
    assert res.status == Status.ERRO


def test_decadencia_com_prazo_longo_nao_e_erro():
    m = _minuta(
        "Processo nº 5018899-65.2025.4.03.6183\nDER: 20/06/2001\n"
        "II.4 - Da Decadência\ndecaiu o direito...\n"
    )
    (res,) = DecadenciaImpossivelPorDatas().verificar(m)
    assert res.status == Status.INFO


def test_decadencia_ausente_e_info():
    m = _minuta(_CABECALHO_JEF)
    (res,) = DecadenciaImpossivelPorDatas().verificar(m)
    assert res.status == Status.INFO


# ---- 3.5 ruído: limiar por janela temporal ---------------------------------

def test_ruido_90db_em_periodo_pos_2003_gera_erro():
    m = _minuta(_bloco_ruido(
        "10/01/2006 a 20/03/2021",
        "1. Exposição ao ruído dentro do limite de tolerância - 90 dB(A).",
    ))
    (res,) = RuidoLimiarPorPeriodo().verificar(m)
    assert res.status == Status.ERRO
    assert "85" in res.mensagem


def test_ruido_90db_em_janela_correta_ok():
    m = _minuta(_bloco_ruido(
        "06/03/1997 a 31/12/2002",
        "1. Exposição ao ruído dentro do limite de tolerância - 90 dB(A).",
    ))
    (res,) = RuidoLimiarPorPeriodo().verificar(m)
    assert res.status == Status.OK


def test_ruido_cruzando_marco_vira_verificar():
    m = _minuta(_bloco_ruido(
        "01/03/1990 a 20/10/1998",
        "1. Exposição ao ruído dentro do limite de tolerância - 90 dB(A).",
    ))
    (res,) = RuidoLimiarPorPeriodo().verificar(m)
    assert res.status == Status.VERIFICAR


# ---- 3.5 ruído: metodologia por janela temporal ----------------------------

def test_nr15_em_periodo_pos_2003_gera_erro():
    m = _minuta(_bloco_ruido(
        "10/01/2006 a 20/03/2021",
        "3. As aferições devem obediência à NR-15.",
    ))
    (res,) = RuidoMetodologiaPorPeriodo().verificar(m)
    assert res.status == Status.ERRO


def test_nen_nho01_em_periodo_pos_2003_ok():
    m = _minuta(_bloco_ruido(
        "19/11/2003 a 20/03/2021",
        "3. É obrigatória a indicação em NEN, conforme a NHO-01 da FUNDACENTRO.",
    ))
    (res,) = RuidoMetodologiaPorPeriodo().verificar(m)
    assert res.status == Status.OK


def test_nr15_em_periodo_anterior_ok():
    m = _minuta(_bloco_ruido(
        "06/03/1997 a 31/12/2002",
        "3. As aferições devem obediência à NR-15.",
    ))
    (res,) = RuidoMetodologiaPorPeriodo().verificar(m)
    assert res.status == Status.OK


# ---- 3.6 calor: limiar por janela temporal ---------------------------------

def _bloco_calor(periodo: str, tese: str) -> str:
    ini, fim = periodo.split(" a ")
    return (
        "III - DO MÉRITO\n"
        f"III.1 - Período de {ini} a {fim} - Agente: Calor\n"
        f"Agentes Nocivos:\n{tese}\n"
    )


def test_calor_24_7_em_periodo_anterior_a_2019_gera_erro():
    m = _minuta(_bloco_calor(
        "06/03/1997 a 30/06/2010", "1. A exposição é inferior a 24,7 ºC."
    ))
    (res,) = CalorLimiarPorPeriodo().verificar(m)
    assert res.status == Status.ERRO
    assert "25" in res.mensagem


def test_calor_25_em_janela_correta_ok():
    m = _minuta(_bloco_calor(
        "01/01/2003 a 30/06/2018", "1. A exposição é inferior a 25 ºC."
    ))
    (res,) = CalorLimiarPorPeriodo().verificar(m)
    assert res.status == Status.OK


# ---- 3.3 vício CREA/CRM -----------------------------------------------------

def test_vicio_crea_crm_gera_erro():
    m = _minuta("1. O responsável não possui registro no CRM ou no CREA.")
    (res,) = VicioCreaCrm().verificar(m)
    assert res.status == Status.ERRO


def test_sem_crea_crm_ok():
    m = _minuta("1. A parte autora não comprova poderes de representação.")
    (res,) = VicioCreaCrm().verificar(m)
    assert res.status == Status.OK


# ---- 3.17 vedação à conversão -----------------------------------------------

def test_periodo_pos_2019_sem_vedacao_gera_erro():
    m = _minuta(_bloco_ruido("10/01/2006 a 20/03/2021", "1. teses."))
    (res,) = VedacaoConversaoPos2019().verificar(m)
    assert res.status == Status.ERRO


def test_periodo_pos_2019_com_vedacao_ok():
    m = _minuta(
        _bloco_ruido("10/01/2006 a 20/03/2021", "1. teses.")
        + "IV - OUTROS FUNDAMENTOS\nFica vedada a conversão de tempo especial "
        "em comum para períodos posteriores a 13/11/2019.\n"
    )
    (res,) = VedacaoConversaoPos2019().verificar(m)
    assert res.status == Status.OK


def test_vedacao_presente_sem_periodo_pos_2019_nao_e_erro():
    # fundamento padrão tolerado (gabarito da minuta de teste)
    m = _minuta(
        _bloco_ruido("06/03/1997 a 31/12/2002", "1. teses.")
        + "IV - OUTROS FUNDAMENTOS\nFica vedada a conversão de tempo especial em comum.\n"
    )
    (res,) = VedacaoConversaoPos2019().verificar(m)
    assert res.status == Status.OK


# ---- 3.1 consistência síntese × tabela --------------------------------------

def test_divergencia_sintese_tabela_gera_erros():
    m = _minuta(
        "I - SÍNTESE DA DEMANDA\n"
        "alegando exposição nos períodos de 06/03/1997 a 31/12/2002 e de "
        "01/01/2003 a 30/06/2015.\n"
        + _bloco_ruido("06/03/1997 a 31/12/2002", "1. teses.")
        + "III.2 - Período de 02/01/2016 a 18/12/2020 - Agente: Ruído\n..."
    )
    res = ConsistenciaSinteseTabela().verificar(m)
    status = {r.id: r.status for r in res}
    assert status["3.1-consistencia-sintese-tabela:omitidos"] == Status.ERRO
    assert status["3.1-consistencia-sintese-tabela:nao-pedidos"] == Status.ERRO


def test_sintese_e_tabela_coerentes_ok():
    m = _minuta(
        "I - SÍNTESE DA DEMANDA\n"
        "alegando exposição no período de 06/03/1997 a 31/12/2002.\n"
        + _bloco_ruido("06/03/1997 a 31/12/2002", "1. teses.")
    )
    (res,) = ConsistenciaSinteseTabela().verificar(m)
    assert res.status == Status.OK


# ---- 6.4 sem pedido de tempo especial / 7.1 indeferimento forçado -----------

def test_sem_pedido_de_tempo_especial_gera_erro():
    m = _minuta(
        "I - SÍNTESE DA DEMANDA\npleiteia tão somente a averbação, não havendo "
        "pedido de reconhecimento de tempo especial na petição inicial.\n"
    )
    (res,) = SemPedidoTempoEspecial().verificar(m)
    assert res.status == Status.ERRO


def test_indeferimento_forcado_gera_erro():
    m = _minuta(
        'I - SÍNTESE DA DEMANDA\n[Análise do PA: à pergunta "Possui tempo '
        'especial?" consta resposta "Não"; não houve análise técnica de tempo '
        "especial no processo administrativo.]\n"
    )
    (res,) = IndeferimentoForcado().verificar(m)
    assert res.status == Status.ERRO


def test_indeferimento_sem_sinais_e_info():
    m = _minuta("I - SÍNTESE DA DEMANDA\ncaso comum de aposentadoria especial.\n")
    (res,) = IndeferimentoForcado().verificar(m)
    assert res.status == Status.INFO
