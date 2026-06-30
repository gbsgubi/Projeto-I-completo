"""Bloco 6 — Verificações especiais de redistribuição.

Detecta perfis que, em vez de contestação normal, exigem etiquetagem e
redistribuição para equipe específica. Cada achado é reportado como
"redistribuição sugerida" (status INFO), nunca como erro — a redistribuição em
si é ação manual do estagiário no SAPIENS.

  - VIGILANTE: vigilante, vigia, guarda, policial.
  - SAÚDE: profissional/ambiente de saúde + menção a agente biológico.
  - PROFESSOR: professor com indício de período posterior a 1981.
"""

from __future__ import annotations

import re

from ..report import Resultado, Status
from ..segmenter import Minuta
from ..utils import normalizar, primeiro_trecho
from . import Regra, registrar

BLOCO = "Bloco 6 - Redistribuição"

_TERMOS_VIGILANTE = ["vigilante", "vigia", "guarda", "policial"]
_TERMOS_SAUDE = [
    "enfermeiro", "enfermeira", "auxiliar de enfermagem", "tecnico de enfermagem",
    "medico", "medica", "dentista", "odontolog", "veterinari",
    "hospital", "clinica", "pronto-socorro", "pronto socorro", "ambulancia",
    "laboratorio", "estabelecimento de saude", "ambiente hospitalar",
]
_TERMOS_BIOLOGICO = ["agente biologico", "agentes biologicos", "biologico"]


@registrar
class RedistribuicaoVigilante(Regra):
    id = "6.1-vigilante"
    bloco = BLOCO
    descricao = "Indício de categoria vigilante/vigia/guarda/policial"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        norm = normalizar(minuta.texto)
        achados = [t for t in _TERMOS_VIGILANTE if re.search(rf"\b{t}\b", norm)]
        if achados:
            ev = primeiro_trecho(minuta.texto, rf"\b({'|'.join(achados)})\b")
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.INFO,
                    f"Redistribuição sugerida — flag VIGILANTE "
                    f"(termo(s): {', '.join(achados)}).",
                    ev,
                )
            ]
        return [
            Resultado(
                self.id, self.bloco, self.descricao, Status.OK,
                "Sem indício de categoria vigilante/vigia/guarda/policial.",
                None,
            )
        ]


@registrar
class RedistribuicaoSaude(Regra):
    id = "6.2-saude"
    bloco = BLOCO
    descricao = "Indício de profissional/ambiente de saúde + agente biológico"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        norm = normalizar(minuta.texto)
        saude = [t for t in _TERMOS_SAUDE if t in norm]
        biologico = any(t in norm for t in _TERMOS_BIOLOGICO)
        if saude and biologico:
            ev = primeiro_trecho(minuta.texto, rf"({'|'.join(re.escape(s) for s in saude)})")
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.INFO,
                    f"Redistribuição sugerida — flag SAÚDE "
                    f"(indício(s): {', '.join(saude)} + agente biológico).",
                    ev,
                )
            ]
        return [
            Resultado(
                self.id, self.bloco, self.descricao, Status.OK,
                "Sem indício combinado de profissional de saúde e agente biológico.",
                None,
            )
        ]


@registrar
class RedistribuicaoProfessor(Regra):
    id = "6.3-professor"
    bloco = BLOCO
    descricao = "Indício de professor com período posterior a 1981"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        norm = normalizar(minuta.texto)
        tem_professor = re.search(r"\bprofessor\w*\b", norm) is not None
        # algum ano > 1981 no texto
        anos = [int(a) for a in re.findall(r"\b(19[89]\d|20\d\d)\b", minuta.texto)]
        posterior_1981 = any(a > 1981 for a in anos)
        if tem_professor and posterior_1981:
            ev = primeiro_trecho(minuta.texto, r"\bprofessor\w*")
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.INFO,
                    "Redistribuição sugerida — flag PROFESSOR "
                    "(professor com indício de período posterior a 1981).",
                    ev,
                )
            ]
        return [
            Resultado(
                self.id, self.bloco, self.descricao, Status.OK,
                "Sem indício de professor em período posterior a 1981.",
                None,
            )
        ]
