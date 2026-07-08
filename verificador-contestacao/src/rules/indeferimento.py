"""Bloco 7 — Indeferimento forçado (minuta nº 618527).

Quando o PA registra "Possui tempo especial? NÃO" e não houve análise técnica
de tempo especial, o caso é de INDEFERIMENTO FORÇADO: usa-se a minuta nº
618527, e não a contestação padrão (nº 544316).

Essas condições vivem no PA (externo à minuta) — em regra a checagem depende
de contexto. A regra abaixo só decide quando os sinais estão declarados no
próprio texto da peça (como nos casos de teste autossuficientes); sem os
sinais, nada é acusado e a conferência permanece manual/fase do LLM.
"""

from __future__ import annotations

import re

from ..report import Resultado, Status
from ..segmenter import Minuta
from ..utils import normalizar, primeiro_trecho
from . import Regra, registrar

BLOCO = "Bloco 7 - Indeferimento forçado"

_RE_RESPOSTA_NAO = re.compile(r"possui tempo especial[^a-z]*(?:consta )?resposta\s*\"?nao\"?")
_SINAIS_SEM_ANALISE = [
    "nao houve analise tecnica",
    "sem analise tecnica",
    "nao ha analise tecnica",
]


@registrar
class IndeferimentoForcado(Regra):
    id = "7.1-indeferimento-forcado"
    bloco = BLOCO
    descricao = "Caso de indeferimento forçado tratado como contestação padrão"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        norm = normalizar(minuta.texto)
        resposta_nao = (
            _RE_RESPOSTA_NAO.search(norm) is not None
            or ("possui tempo especial" in norm and 'resposta "nao"' in norm)
        )
        sem_analise = any(s in norm for s in _SINAIS_SEM_ANALISE)

        if resposta_nao and sem_analise:
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.ERRO,
                    "O texto registra que o PA respondeu 'Possui tempo especial? "
                    "NÃO' e que NÃO houve análise técnica de tempo especial — "
                    "caso de INDEFERIMENTO FORÇADO (minuta nº 618527); a "
                    "contestação padrão (nº 544316) é indevida (regra 7.1).",
                    primeiro_trecho(minuta.texto, r"[Pp]ossui tempo especial[^\n]*"),
                )
            ]
        return [
            Resultado(
                self.id, self.bloco, self.descricao, Status.INFO,
                "Sem sinais de indeferimento forçado no texto da minuta; as "
                "condições vivem no PA e a conferência é manual/fase do LLM.",
                None,
            )
        ]
