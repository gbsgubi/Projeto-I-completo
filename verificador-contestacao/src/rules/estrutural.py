"""Bloco 1 — Verificações estruturais da minuta.

Inclui:
  - 1.1 Endereçamento (JEF x Justiça Federal comum).
  - 1.2 Campos obrigatórios de identificação (NB, DER, processo, autor,
    tipo de benefício) via regex.
  - 1.3 Marcações de edição não removidas (colchetes, placeholders, instruções
    imperativas remanescentes e destaque amarelo no HTML).
"""

from __future__ import annotations

import re

from ..report import Resultado, Status
from ..segmenter import Minuta
from ..utils import normalizar, primeiro_trecho
from . import Regra, registrar

BLOCO = "Bloco 1 - Estrutural"


@registrar
class Enderecamento(Regra):
    id = "1.1-enderecamento"
    bloco = BLOCO
    descricao = "Tipo de endereçamento (JEF x Justiça Federal comum)"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        norm = normalizar(minuta.texto)
        if "juizado especial federal" in norm:
            ev = primeiro_trecho(minuta.texto, r"juizado especial federal")
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.INFO,
                    "Endereçamento identificado: JEF (Juizado Especial Federal).",
                    ev,
                )
            ]
        if "subsecao judiciaria" in norm or "vara federal" in norm:
            ev = primeiro_trecho(minuta.texto, r"subse[cç][aã]o judici[aá]ria|vara federal")
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.INFO,
                    "Endereçamento identificado: Justiça Federal comum "
                    "(sem menção a JEF).",
                    ev,
                )
            ]
        return [
            Resultado(
                self.id, self.bloco, self.descricao, Status.VERIFICAR,
                "Não foi possível determinar o tipo de endereçamento; "
                "verificar manualmente.",
                None,
            )
        ]


# Campos obrigatórios: (rótulo, regex aplicada ao TEXTO ORIGINAL).
_CAMPOS = [
    ("NB", r"\bNB[:\s]"),
    ("DER", r"\bDER[:\s]"),
    (
        "Número do processo",
        r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b",
    ),
    ("Nome do autor", r"que lhe move\s+[A-ZÀ-Ú][A-ZÀ-Ú\s]{4,}"),
    (
        "Tipo de benefício",
        r"(concess[aã]o|revis[aã]o|aposentadoria especial|"
        r"tempo de contribui[cç][aã]o|tempo especial)",
    ),
]


@registrar
class CamposObrigatorios(Regra):
    id = "1.2-campos-obrigatorios"
    bloco = BLOCO
    descricao = "Campos obrigatórios de identificação (NB, DER, processo, autor, benefício)"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        resultados: list[Resultado] = []
        for rotulo, padrao in _CAMPOS:
            m = re.search(padrao, minuta.texto, flags=re.IGNORECASE)
            if m:
                ev = primeiro_trecho(minuta.texto, padrao)
                resultados.append(
                    Resultado(
                        f"{self.id}:{normalizar(rotulo).replace(' ', '-')}",
                        self.bloco,
                        f"Campo obrigatório: {rotulo}",
                        Status.OK,
                        f"{rotulo} presente.",
                        ev,
                    )
                )
            else:
                resultados.append(
                    Resultado(
                        f"{self.id}:{normalizar(rotulo).replace(' ', '-')}",
                        self.bloco,
                        f"Campo obrigatório: {rotulo}",
                        Status.ERRO,
                        f"{rotulo} ausente na minuta.",
                        None,
                    )
                )
        return resultados


# Padrões de marcação de edição não removida.
_PADRAO_COLCHETES = re.compile(r"\[[^\]\n]{3,}\]")
_PADRAO_PLACEHOLDER_X = re.compile(r"\bX{4,}\b", re.IGNORECASE)
# underscore "em branco" dentro de uma linha que tem outro conteúdo textual
# (a linha de assinatura, formada só por underscores, é ignorada).
_PADRAO_PLACEHOLDER_UNDERSCORE = re.compile(r"_{4,}")
_INSTRUCOES_IMPERATIVAS = [
    r"\bVERIFICAR\b",
    r"\bATEN[CÇ][AÃ]O\b",
    r"\bPREENCHER\b",
    r"\bdeixar a preliminar\b",
    r"\bINSERIR\b",
    r"\bCONFERIR\b",
]


def _linha_so_underscore(texto: str, pos: int) -> bool:
    """True se o underscore em ``pos`` está numa linha composta só por _ e espaço
    (linha de assinatura), que não deve ser tratada como placeholder."""
    ini = texto.rfind("\n", 0, pos) + 1
    fim = texto.find("\n", pos)
    if fim == -1:
        fim = len(texto)
    linha = texto[ini:fim]
    return re.fullmatch(r"[\s_]+", linha) is not None


@registrar
class MarcacoesEdicao(Regra):
    id = "1.3-marcacoes-edicao"
    bloco = BLOCO
    descricao = "Marcações de edição não removidas (colchetes, placeholders, instruções, amarelo)"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        achados: list[str] = []

        # destaque amarelo (apenas HTML; no PDF vira texto comum)
        for trecho in minuta.destaques_amarelos:
            achados.append(f"destaque amarelo: \"{trecho}\"")

        # colchetes [...]
        for m in _PADRAO_COLCHETES.finditer(minuta.texto):
            achados.append(f"colchetes: \"{m.group(0)}\"")

        # placeholder XXXX
        for m in _PADRAO_PLACEHOLDER_X.finditer(minuta.texto):
            achados.append(f"placeholder: \"{m.group(0)}\"")

        # placeholder ____ (ignorando linha de assinatura)
        for m in _PADRAO_PLACEHOLDER_UNDERSCORE.finditer(minuta.texto):
            if not _linha_so_underscore(minuta.texto, m.start()):
                achados.append("placeholder de preenchimento (sublinhado em branco)")

        # instruções imperativas remanescentes
        for padrao in _INSTRUCOES_IMPERATIVAS:
            ev = primeiro_trecho(minuta.texto, padrao, contexto=40)
            if ev is not None:
                achados.append(f"instrução remanescente: \"{ev}\"")

        # de-duplica preservando ordem
        vistos: set[str] = set()
        unicos = [a for a in achados if not (a in vistos or vistos.add(a))]

        if unicos:
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.ERRO,
                    f"Há {len(unicos)} marcação(ões) de edição não removida(s) "
                    "na minuta — devem ser eliminadas antes do envio.",
                    " | ".join(unicos[:6]),
                )
            ]
        return [
            Resultado(
                self.id, self.bloco, self.descricao, Status.OK,
                "Nenhuma marcação de edição remanescente detectada.",
                None,
            )
        ]
