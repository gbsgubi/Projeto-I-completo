"""Catalogação de teses padronizadas (Blocos 3, 4 e 5).

Nesta fase apenas CATALOGAMOS quais teses padronizadas aparecem no texto
(padrão de nome começando por ``CTN-``, ``DIVESP-NOTA-``, etc.). NÃO avaliamos
se a tese é compatível com o agente/período — essa análise é da fase do LLM
(ver ``llm_stubs.py``).
"""

from __future__ import annotations

import re

from ..report import Resultado, Status
from ..segmenter import Minuta
from . import Regra, registrar

BLOCO = "Teses presentes (Blocos 3/4/5 - catalogação)"

# Nomes de tese padronizados. Prefixos conhecidos seguidos de letras
# maiúsculas, dígitos, hífens, espaços e acentos.
_RE_TESE = re.compile(
    r"\b(?:CTN|DIVESP-NOTA|DIVESP|SEAS)[-–][A-ZÀ-Ú0-9][A-ZÀ-Ú0-9ÇÃÕÁÉÍÓÚÂÊÔÀ\-–/ ]{3,}",
)


def _limpar(nome: str) -> str:
    return re.sub(r"\s+", " ", nome).strip(" -–/")


@registrar
class CatalogacaoTeses(Regra):
    id = "345-catalogo-teses"
    bloco = BLOCO
    descricao = "Catalogação das teses padronizadas presentes (CTN-/DIVESP- etc.)"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        encontradas: list[str] = []
        vistos: set[str] = set()
        for m in _RE_TESE.finditer(minuta.texto):
            nome = _limpar(m.group(0))
            chave = nome.upper()
            if chave not in vistos:
                vistos.add(chave)
                encontradas.append(nome)

        if encontradas:
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.INFO,
                    f"{len(encontradas)} tese(s) padronizada(s) catalogada(s).",
                    " | ".join(encontradas),
                )
            ]
        return [
            Resultado(
                self.id, self.bloco, self.descricao, Status.INFO,
                "Nenhuma tese padronizada (CTN-/DIVESP-) encontrada no texto. "
                "A minuta de teste usa fundamentos em prosa, sem códigos de tese.",
                None,
            )
        ]
