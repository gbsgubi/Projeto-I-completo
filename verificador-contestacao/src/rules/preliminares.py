"""Bloco 2 — Preliminares processuais.

Além da catalogação de PRESENÇA/AUSÊNCIA de cada preliminar, esta fase aplica
as correlações que são puramente determinísticas (não dependem de contexto
externo à minuta nem de raciocínio de LLM):

  - 2.1/2.2: Juízo 100% Digital e Audiência de Conciliação são SEMPRE
    obrigatórias — ausência é ERRO.
  - 2.3: Renúncia aos 60 SM é obrigatória no JEF (ausência é ERRO) e indevida
    na Justiça Federal comum (presença é ERRO).
  - 2.4: Decadência presente quando as datas da própria minuta (DER × ano de
    ajuizamento) tornam o prazo de 10 anos impossível é ERRO. O caso inverso
    (decadência AUSENTE quando cabível) continua na fase do LLM, pois depende
    da data da primeira prestação, que não consta da minuta.
"""

from __future__ import annotations

import re

from ..report import Resultado, Status
from ..segmenter import Minuta
from ..utils import normalizar
from . import Regra, registrar

BLOCO = "Bloco 2 - Preliminares (presença)"

# Cada preliminar: (id, nome, lista de padrões — basta um casar no texto
# normalizado sem acentos para considerar PRESENTE).
PRELIMINARES = [
    ("juizo-digital", "Juízo 100% Digital",
     ["juizo 100% digital", "juizo 100 digital", "100% digital", "tramitacao digital"]),
    ("conciliacao", "Audiência de Conciliação",
     ["audiencia de conciliacao", "interesse na realizacao de audiencia"]),
    ("renuncia-60sm", "Renúncia aos 60 Salários-Mínimos",
     ["renuncia", "sessenta salarios minimos", "60 salarios minimos",
      "montante que ultrapasse sessenta"]),
    ("decadencia", "Decadência", ["decadencia", "decaiu o direito"]),
    ("prescricao", "Prescrição", ["prescricao", "parcelas vencidas anteriormente ao quinquenio"]),
    ("coisa-julgada", "Coisa Julgada", ["coisa julgada"]),
    ("litispendencia", "Litispendência", ["litispendencia"]),
    ("ppp-nao-apresentado", "PPP não apresentado administrativamente",
     ["ppp nao apresentado administrativamente", "nao apresentou formularios",
      "nao apresentou ppp"]),
    ("periodos-reconhecidos", "Períodos reconhecidos administrativamente",
     ["periodos especiais reconhecidos administrativamente",
      "reconhecidos administrativamente"]),
    ("inicial-inepta", "Petição inicial inepta",
     ["peticao inicial inepta", "inicial inepta", "inepcia"]),
]


def _padroes_de(pid: str) -> list[str]:
    for _id, _nome, padroes in PRELIMINARES:
        if _id == pid:
            return padroes
    return []


def _renuncia_padroes() -> list[str]:
    return _padroes_de("renuncia-60sm")


def _presente(norm_texto: str, padroes: list[str]) -> bool:
    return any(p in norm_texto for p in padroes)


@registrar
class PresencaPreliminares(Regra):
    id = "2.0-presenca-preliminares"
    bloco = BLOCO
    descricao = "Presença/ausência de cada preliminar padronizada"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        norm = normalizar(minuta.texto)
        resultados: list[Resultado] = []
        for pid, nome, padroes in PRELIMINARES:
            if _presente(norm, padroes):
                resultados.append(
                    Resultado(
                        f"2.presenca:{pid}", self.bloco,
                        f"Preliminar: {nome}", Status.INFO,
                        "PRESENTE.", None,
                    )
                )
            else:
                resultados.append(
                    Resultado(
                        f"2.presenca:{pid}", self.bloco,
                        f"Preliminar: {nome}", Status.INFO,
                        "AUSENTE.", None,
                    )
                )
        return resultados


# Preliminares que devem estar presentes em TODA contestação (regras 2.1 e
# 2.2): a ausência é erro independentemente de qualquer contexto externo.
_SEMPRE_OBRIGATORIAS = [
    ("juizo-digital", "Juízo 100% Digital", "2.1"),
    ("conciliacao", "Audiência de Conciliação", "2.2"),
]


@registrar
class PreliminaresSempreObrigatorias(Regra):
    id = "2.12-preliminares-sempre-obrigatorias"
    bloco = BLOCO
    descricao = "Preliminares sempre obrigatórias (Juízo 100% Digital e Conciliação)"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        norm = normalizar(minuta.texto)
        resultados: list[Resultado] = []
        for pid, nome, regra in _SEMPRE_OBRIGATORIAS:
            if _presente(norm, _padroes_de(pid)):
                resultados.append(
                    Resultado(
                        f"{regra}-{pid}-obrigatoria", self.bloco,
                        f"Preliminar obrigatória: {nome}", Status.OK,
                        f"Preliminar de {nome} presente (sempre obrigatória).",
                        None,
                    )
                )
            else:
                resultados.append(
                    Resultado(
                        f"{regra}-{pid}-obrigatoria", self.bloco,
                        f"Preliminar obrigatória: {nome}", Status.ERRO,
                        f"A preliminar de {nome} está AUSENTE — ela deve constar "
                        f"de TODA contestação (regra {regra} do manual).",
                        None,
                    )
                )
        return resultados


@registrar
class RenunciaObrigatoriaNoJEF(Regra):
    """Correlação determinística entre endereçamento e Renúncia aos 60 SM:
    obrigatória no JEF, indevida na Justiça Federal comum."""

    id = "2.3-renuncia-jef"
    bloco = BLOCO
    descricao = "Renúncia aos 60 SM obrigatória no JEF (e indevida fora dele)"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        norm = normalizar(minuta.texto)
        eh_jef = "juizado especial federal" in norm
        eh_jf_comum = not eh_jef and (
            "subsecao judiciaria" in norm or "vara federal" in norm
        )
        tem_renuncia = _presente(norm, _renuncia_padroes())

        if eh_jef:
            if tem_renuncia:
                return [
                    Resultado(
                        self.id, self.bloco, self.descricao, Status.OK,
                        "Processo no JEF e preliminar de Renúncia aos 60 SM presente.",
                        None,
                    )
                ]
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.ERRO,
                    "Processo no JEF, mas a preliminar de Renúncia aos 60 "
                    "salários-mínimos está AUSENTE (art. 3º, §2º, Lei 10.259/2001).",
                    None,
                )
            ]
        if eh_jf_comum:
            if tem_renuncia:
                return [
                    Resultado(
                        self.id, self.bloco, self.descricao, Status.ERRO,
                        "Processo na Justiça Federal comum, mas a preliminar de "
                        "Renúncia aos 60 salários-mínimos está PRESENTE — ela só "
                        "se aplica a processos do JEF (regra 2.3).",
                        None,
                    )
                ]
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.OK,
                    "Justiça Federal comum e renúncia aos 60 SM corretamente ausente.",
                    None,
                )
            ]
        return [
            Resultado(
                self.id, self.bloco, self.descricao, Status.VERIFICAR,
                "Endereçamento indeterminado; confirmar manualmente se a "
                "renúncia aos 60 SM se aplica.",
                None,
            )
        ]


# Datas usadas na checagem determinística de decadência.
_RE_DER = re.compile(r"\bDER[:\s]+(\d{2})/(\d{2})/(\d{4})", re.IGNORECASE)
_RE_AJUIZADA_EM = re.compile(r"ajuizad[ao]\s+em\s+(\d{4})", re.IGNORECASE)
# ano de ajuizamento no número CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO
_RE_ANO_CNJ = re.compile(r"\b\d{7}-\d{2}\.(\d{4})\.\d\.\d{2}\.\d{4}\b")


@registrar
class DecadenciaImpossivelPorDatas(Regra):
    """Regra 2.4 (parte determinística): a decadência exige 10 anos entre o
    1º dia do mês seguinte ao recebimento da primeira prestação e o
    ajuizamento. A primeira prestação nunca é anterior à DER; logo, se
    ``ano do ajuizamento - ano da DER < 10``, o prazo é matematicamente
    impossível e a preliminar presente é ERRO. O caso inverso (ausente quando
    cabível) e a distinção concessão × revisão ficam para a fase do LLM."""

    id = "2.4-decadencia-datas"
    bloco = BLOCO
    descricao = "Decadência presente com prazo de 10 anos impossível pelas datas"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        norm = normalizar(minuta.texto)
        tem_decadencia = _presente(norm, _padroes_de("decadencia"))
        if not tem_decadencia:
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.INFO,
                    "Preliminar de decadência ausente; o cabimento da ausência "
                    "depende de dados externos (fase do LLM).",
                    None,
                )
            ]

        m_der = _RE_DER.search(minuta.texto)
        m_ajuizada = _RE_AJUIZADA_EM.search(minuta.texto)
        m_cnj = _RE_ANO_CNJ.search(minuta.texto)
        ano_ajuizamento = int(m_ajuizada.group(1)) if m_ajuizada else (
            int(m_cnj.group(1)) if m_cnj else None
        )
        if not m_der or ano_ajuizamento is None:
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.VERIFICAR,
                    "Preliminar de decadência presente, mas não foi possível "
                    "extrair DER e/ou ano de ajuizamento para validar o prazo; "
                    "confirmar manualmente.",
                    None,
                )
            ]

        ano_der = int(m_der.group(3))
        diferenca = ano_ajuizamento - ano_der
        evidencia = (
            f"DER: {m_der.group(1)}/{m_der.group(2)}/{ano_der} | "
            f"ajuizamento: {ano_ajuizamento}"
        )
        if diferenca < 10:
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.ERRO,
                    "Preliminar de decadência PRESENTE, mas o prazo de 10 anos é "
                    f"impossível: entre a DER ({ano_der}) e o ajuizamento "
                    f"({ano_ajuizamento}) passaram menos de 10 anos, e a primeira "
                    "prestação nunca é anterior à DER (regra 2.4).",
                    evidencia,
                )
            ]
        if diferenca == 10:
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.VERIFICAR,
                    "Decadência presente com exatamente 10 anos entre DER e "
                    "ajuizamento — o cabimento depende do mês/dia; confirmar.",
                    evidencia,
                )
            ]
        return [
            Resultado(
                self.id, self.bloco, self.descricao, Status.INFO,
                "Decadência presente e prazo de 10 anos não descartável pelas "
                "datas da minuta; a confirmação fina fica para a fase do LLM.",
                evidencia,
            )
        ]
