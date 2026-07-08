"""Bloco 6 — Verificações especiais de redistribuição.

Detecta perfis que, em vez de contestação normal, exigem etiquetagem e
redistribuição para equipe específica:

  - VIGILANTE: vigilante, vigia, guarda, policial.
  - SAÚDE: profissional/ambiente de saúde + menção a agente biológico.
  - PROFESSOR: professor com indício de período posterior a 1981.
  - SEM TEMPO ESPECIAL: a inicial não pede reconhecimento de tempo especial.

Gradação determinística: quando o perfil aparece com SINAL FORTE — na
síntese da demanda ou no campo "Agente:" da tabela, ou seja, o próprio
estagiário o declarou —, elaborar a contestação padrão é ERRO (regras
6.1–6.3: "não contestar normalmente; etiquetar e redistribuir"). Quando o
termo só aparece solto em outro trecho, é apenas sugestão (INFO), pois o
indício é fraco e a confirmação exigiria análise contextual.
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


def _texto_sinal_forte(minuta: Minuta) -> str:
    """Texto onde a menção ao perfil caracteriza declaração explícita do caso:
    a síntese da demanda e os campos 'Agente:' da tabela do mérito."""
    agentes = " ".join(p.get("agente", "") for p in minuta.periodos)
    return normalizar(minuta.secao("sintese") + " " + agentes)


@registrar
class RedistribuicaoVigilante(Regra):
    id = "6.1-vigilante"
    bloco = BLOCO
    descricao = "Indício de categoria vigilante/vigia/guarda/policial"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        forte = _texto_sinal_forte(minuta)
        norm = normalizar(minuta.texto)
        no_forte = [t for t in _TERMOS_VIGILANTE if re.search(rf"\b{t}\b", forte)]
        no_texto = [t for t in _TERMOS_VIGILANTE if re.search(rf"\b{t}\b", norm)]
        if no_forte:
            ev = primeiro_trecho(minuta.texto, rf"\b({'|'.join(no_forte)})\b")
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.ERRO,
                    "A síntese/tabela declara categoria de "
                    f"{', '.join(no_forte)} — caso de REDISTRIBUIÇÃO (etiqueta "
                    "VIGILANTE); não se elabora contestação padrão (regra 6.1).",
                    ev,
                )
            ]
        if no_texto:
            ev = primeiro_trecho(minuta.texto, rf"\b({'|'.join(no_texto)})\b")
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.INFO,
                    f"Redistribuição sugerida — flag VIGILANTE "
                    f"(termo(s): {', '.join(no_texto)}).",
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
        forte = _texto_sinal_forte(minuta)
        norm = normalizar(minuta.texto)
        biologico = any(t in norm for t in _TERMOS_BIOLOGICO)
        saude_forte = [t for t in _TERMOS_SAUDE if t in forte]
        saude_fraco = [t for t in _TERMOS_SAUDE if t in norm]
        if saude_forte and biologico:
            ev = primeiro_trecho(
                minuta.texto, rf"({'|'.join(re.escape(s) for s in saude_forte)})"
            )
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.ERRO,
                    "A síntese/tabela declara profissional/ambiente de saúde "
                    f"({', '.join(saude_forte)}) com agente biológico — caso de "
                    "REDISTRIBUIÇÃO (etiqueta SAÚDE); não se elabora contestação "
                    "padrão (regra 6.2).",
                    ev,
                )
            ]
        if saude_fraco and biologico:
            ev = primeiro_trecho(
                minuta.texto, rf"({'|'.join(re.escape(s) for s in saude_fraco)})"
            )
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.INFO,
                    f"Redistribuição sugerida — flag SAÚDE "
                    f"(indício(s): {', '.join(saude_fraco)} + agente biológico).",
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
        forte = _texto_sinal_forte(minuta)
        norm = normalizar(minuta.texto)
        professor_forte = re.search(r"\bprofessor\w*\b|\bmagisterio\b", forte) is not None
        professor_fraco = re.search(r"\bprofessor\w*\b", norm) is not None
        # algum ano > 1981 no texto
        anos = [int(a) for a in re.findall(r"\b(19[89]\d|20\d\d)\b", minuta.texto)]
        posterior_1981 = any(a > 1981 for a in anos)
        if professor_forte and posterior_1981:
            ev = primeiro_trecho(minuta.texto, r"\bprofessor\w*|\bmagist[eé]rio\b")
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.ERRO,
                    "A síntese/tabela declara categoria de professor com período "
                    "posterior a 1981 — caso de REDISTRIBUIÇÃO; não se elabora "
                    "contestação padrão (regra 6.3).",
                    ev,
                )
            ]
        if professor_fraco and posterior_1981:
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


_PADROES_SEM_TEMPO_ESPECIAL = [
    "nao havendo pedido de reconhecimento de tempo especial",
    "nao ha pedido de reconhecimento de tempo especial",
    "nao ha pedido de tempo especial",
    "sem pedido de tempo especial",
]


@registrar
class SemPedidoTempoEspecial(Regra):
    """Regra 6.4 (Manual, p. 11): se a inicial não pede reconhecimento de
    tempo especial, o caso é de redistribuição — a contestação padrão de
    aposentadoria especial é indevida. Determinístico quando a própria
    síntese declara a ausência do pedido."""

    id = "6.4-sem-pedido-tempo-especial"
    bloco = BLOCO
    descricao = "Inicial sem pedido de tempo especial (caso de redistribuição)"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        norm = normalizar(minuta.texto)
        achado = next((p for p in _PADROES_SEM_TEMPO_ESPECIAL if p in norm), None)
        if achado:
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.ERRO,
                    "A síntese declara que NÃO há pedido de reconhecimento de "
                    "tempo especial na inicial — caso de REDISTRIBUIÇÃO; a "
                    "contestação padrão de aposentadoria especial é indevida.",
                    primeiro_trecho(
                        minuta.texto,
                        r"n[aã]o havendo pedido de reconhecimento[^\n]*",
                    ),
                )
            ]
        return [
            Resultado(
                self.id, self.bloco, self.descricao, Status.OK,
                "Sem declaração de ausência de pedido de tempo especial.",
                None,
            )
        ]
