"""Bloco 2 — Preliminares processuais (somente PRESENÇA).

Esta fase detecta apenas se cada preliminar está PRESENTE ou AUSENTE, por nome
de tese e/ou trecho característico. NÃO decide ainda se a preliminar *deveria*
estar presente (isso depende de contexto e datas — fica para a fase do LLM,
ver ``llm_stubs.py``).

Exceção determinística: se o endereçamento é JEF e a preliminar de Renúncia aos
60 salários-mínimos está ausente, isso é um ERRO (correlação puramente
estrutural, art. 3º, §2º, Lei 10.259/2001).
"""

from __future__ import annotations

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


def _renuncia_padroes() -> list[str]:
    for _id, _nome, padroes in PRELIMINARES:
        if _id == "renuncia-60sm":
            return padroes
    return []


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


@registrar
class RenunciaObrigatoriaNoJEF(Regra):
    """Exceção determinística: JEF exige a preliminar de Renúncia aos 60 SM."""

    id = "2.3-renuncia-jef"
    bloco = BLOCO
    descricao = "Renúncia aos 60 SM obrigatória quando o juízo é o JEF"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        norm = normalizar(minuta.texto)
        eh_jef = "juizado especial federal" in norm
        if not eh_jef:
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.INFO,
                    "Não é JEF; a exigência de renúncia aos 60 SM não se aplica.",
                    None,
                )
            ]
        tem_renuncia = _presente(norm, _renuncia_padroes())
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
