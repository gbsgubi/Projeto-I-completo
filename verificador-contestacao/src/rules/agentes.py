"""Bloco 3 — Verificações determinísticas da tabela de agentes nocivos.

Todas as regras deste módulo decidem apenas com aritmética de datas e
casamento de padrões sobre o texto da própria minuta — nada depende de
contexto externo nem de LLM. O critério de certeza é estrito:

  - Limiar de ruído/calor: só vira ERRO quando o período do bloco está
    INTEIRAMENTE dentro de uma única janela temporal e o valor declarado não
    é o daquela janela. Período que cruza um marco temporal vira VERIFICAR
    (a análise da transição fica para a fase do LLM).
  - Metodologia de ruído: só vira ERRO quando o período é inteiramente
    posterior a 18/11/2003 e o bloco invoca a NR-15 sem mencionar NEN/NHO-01.
  - Vício CREA/CRM: casamento literal — o manual aboliu esse vício.
  - Vedação à conversão (EC 103/2019): ERRO apenas quando algum período
    ultrapassa 13/11/2019 e não há menção à vedação. A presença da vedação
    sem período que a exija NÃO é erro (é fundamento padrão tolerado).
  - Consistência síntese × tabela: ERRO quando os períodos enumerados na
    síntese da demanda divergem dos períodos da tabela do mérito (a cobertura
    contra a petição inicial, externa à minuta, continua na fase do LLM).
"""

from __future__ import annotations

import re
from datetime import date

from ..report import Resultado, Status
from ..segmenter import Minuta
from ..utils import normalizar, primeiro_trecho
from . import Regra, registrar

BLOCO = "Bloco 3 - Agentes nocivos (determinístico)"


def _data(txt: str) -> date | None:
    """Converte 'dd/mm/aaaa' em ``date`` (None se inválida)."""
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", txt.strip())
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def _janelas_do_periodo(
    ini: date, fim: date, janelas: list[tuple[date | None, date | None, object]]
) -> list[object]:
    """Devolve os valores esperados das janelas que o período [ini, fim] toca."""
    tocadas = []
    for j_ini, j_fim, valor in janelas:
        comeco = j_ini or date.min
        termino = j_fim or date.max
        if ini <= termino and fim >= comeco:
            tocadas.append(valor)
    return tocadas


# ---------------------------------------------------------------------------
# 3.5 — RUÍDO: limite de tolerância por marco temporal
# ---------------------------------------------------------------------------

# (início da janela, fim da janela, limite esperado em dB)
_JANELAS_RUIDO = [
    (None, date(1997, 3, 5), 80),
    (date(1997, 3, 6), date(2003, 11, 18), 90),
    (date(2003, 11, 19), None, 85),
]

_RE_DB_DECLARADO = re.compile(r"limite de tolerancia[^0-9]*?(\d{2,3})\s*db")


def _blocos_de_agente(minuta: Minuta, termo: str) -> list[dict]:
    return [
        p for p in minuta.periodos
        if termo in normalizar(p.get("agente", ""))
    ]


@registrar
class RuidoLimiarPorPeriodo(Regra):
    id = "3.5-ruido-limiar"
    bloco = BLOCO
    descricao = "Limite de tolerância do ruído compatível com o marco temporal"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        resultados: list[Resultado] = []
        for p in _blocos_de_agente(minuta, "ruido"):
            ini, fim = _data(p["inicio"]), _data(p["fim"])
            rotulo = f"{p['inicio']} a {p['fim']}"
            if not ini or not fim:
                continue
            m = _RE_DB_DECLARADO.search(normalizar(p["texto"]))
            if not m:
                continue  # sem tese de limite declarada; nada a validar
            declarado = int(m.group(1))
            esperados = _janelas_do_periodo(ini, fim, _JANELAS_RUIDO)
            if len(esperados) > 1:
                resultados.append(
                    Resultado(
                        f"{self.id}:{p['inicio']}", self.bloco, self.descricao,
                        Status.VERIFICAR,
                        f"O período {rotulo} cruza marco(s) temporal(is) do ruído; "
                        "a tese de limite declarada "
                        f"({declarado} dB) precisa de análise da transição "
                        "(fase do LLM).",
                        None,
                    )
                )
            elif esperados and declarado != esperados[0]:
                sufixo = " NEN" if esperados[0] == 85 else ""
                resultados.append(
                    Resultado(
                        f"{self.id}:{p['inicio']}", self.bloco, self.descricao,
                        Status.ERRO,
                        f"Limite de tolerância ERRADO para o período {rotulo}: "
                        f"declarado {declarado} dB(A), mas o correto para o marco "
                        f"temporal é {esperados[0]} dB(A){sufixo} (regra 3.5).",
                        primeiro_trecho(p["texto"], r"limite de toler[^\n]*"),
                    )
                )
            else:
                resultados.append(
                    Resultado(
                        f"{self.id}:{p['inicio']}", self.bloco, self.descricao,
                        Status.OK,
                        f"Limite de tolerância do ruído ({declarado} dB) correto "
                        f"para o período {rotulo}.",
                        None,
                    )
                )
        return resultados


# ---------------------------------------------------------------------------
# 3.5 — RUÍDO: metodologia de aferição por marco temporal
# ---------------------------------------------------------------------------

_MARCO_NEN = date(2003, 11, 19)


@registrar
class RuidoMetodologiaPorPeriodo(Regra):
    id = "3.5-ruido-metodologia"
    bloco = BLOCO
    descricao = "Metodologia de aferição do ruído compatível com o marco temporal"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        resultados: list[Resultado] = []
        for p in _blocos_de_agente(minuta, "ruido"):
            ini, fim = _data(p["inicio"]), _data(p["fim"])
            if not ini or not fim:
                continue
            norm = normalizar(p["texto"])
            cita_nr15 = "nr-15" in norm or "nr 15" in norm
            cita_nen = re.search(r"\bnen\b", norm) or "nho-01" in norm or "nho 01" in norm
            rotulo = f"{p['inicio']} a {p['fim']}"

            if ini >= _MARCO_NEN and cita_nr15 and not cita_nen:
                resultados.append(
                    Resultado(
                        f"{self.id}:{p['inicio']}", self.bloco, self.descricao,
                        Status.ERRO,
                        f"Metodologia ERRADA para o período {rotulo}: o bloco "
                        "invoca a NR-15, mas para períodos posteriores a "
                        "18/11/2003 exige-se NEN/NHO-01 da FUNDACENTRO "
                        "(Decreto nº 4.882/03 — regra 3.5).",
                        primeiro_trecho(p["texto"], r"NR-?\s?15[^\n]*"),
                    )
                )
            elif ini >= _MARCO_NEN and cita_nen:
                resultados.append(
                    Resultado(
                        f"{self.id}:{p['inicio']}", self.bloco, self.descricao,
                        Status.OK,
                        f"Metodologia (NEN/NHO-01) correta para o período {rotulo}.",
                        None,
                    )
                )
            elif fim < _MARCO_NEN and cita_nr15:
                resultados.append(
                    Resultado(
                        f"{self.id}:{p['inicio']}", self.bloco, self.descricao,
                        Status.OK,
                        f"Metodologia (NR-15) compatível com o período {rotulo} "
                        "(anterior a 19/11/2003).",
                        None,
                    )
                )
        return resultados


# ---------------------------------------------------------------------------
# 3.6 — CALOR: limiar de temperatura por marco temporal
# ---------------------------------------------------------------------------

_JANELAS_CALOR = [
    (None, date(1997, 3, 5), 28.0),
    (date(1997, 3, 6), date(2019, 12, 10), 25.0),
    (date(2019, 12, 11), None, 24.7),
]

# após normalizar(), "inferior a 25 ºC" vira "inferior a 25 oc" (º ordinal
# decompõe em "o") ou "inferior a 25 c" (° degree sign é descartado).
_RE_TEMP_DECLARADA = re.compile(r"inferior a (\d{2}(?:[.,]\d)?)\s*o?\s*c\b")


@registrar
class CalorLimiarPorPeriodo(Regra):
    id = "3.6-calor-limiar"
    bloco = BLOCO
    descricao = "Limiar de temperatura do calor compatível com o marco temporal"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        resultados: list[Resultado] = []
        for p in _blocos_de_agente(minuta, "calor"):
            ini, fim = _data(p["inicio"]), _data(p["fim"])
            rotulo = f"{p['inicio']} a {p['fim']}"
            if not ini or not fim:
                continue
            m = _RE_TEMP_DECLARADA.search(normalizar(p["texto"]))
            if not m:
                continue
            declarado = float(m.group(1).replace(",", "."))
            esperados = _janelas_do_periodo(ini, fim, _JANELAS_CALOR)
            if len(esperados) > 1:
                resultados.append(
                    Resultado(
                        f"{self.id}:{p['inicio']}", self.bloco, self.descricao,
                        Status.VERIFICAR,
                        f"O período {rotulo} cruza marco(s) temporal(is) do calor; "
                        f"o limiar declarado ({m.group(1)} ºC) precisa de análise "
                        "da transição (fase do LLM).",
                        None,
                    )
                )
            elif esperados and abs(declarado - esperados[0]) > 0.01:
                esperado_txt = f"{esperados[0]:g}".replace(".", ",")
                resultados.append(
                    Resultado(
                        f"{self.id}:{p['inicio']}", self.bloco, self.descricao,
                        Status.ERRO,
                        f"Limiar de temperatura ERRADO para o período {rotulo}: "
                        f"declarado {m.group(1)} ºC, mas o correto para o marco "
                        f"temporal é {esperado_txt} ºC (regra 3.6).",
                        primeiro_trecho(p["texto"], r"inferior a [^\n]*"),
                    )
                )
            else:
                resultados.append(
                    Resultado(
                        f"{self.id}:{p['inicio']}", self.bloco, self.descricao,
                        Status.OK,
                        f"Limiar de temperatura ({m.group(1)} ºC) correto para o "
                        f"período {rotulo}.",
                        None,
                    )
                )
        return resultados


# ---------------------------------------------------------------------------
# 3.3 — Vício obsoleto: registro no CREA/CRM
# ---------------------------------------------------------------------------


@registrar
class VicioCreaCrm(Regra):
    id = "3.3-vicio-crea-crm"
    bloco = BLOCO
    descricao = "Vício obsoleto de registro no CREA/CRM (não se usa mais)"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        norm = normalizar(minuta.texto)
        if re.search(r"\b(crea|crm)\b", norm):
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.ERRO,
                    "A minuta usa o vício de falta de registro no CREA/CRM — o "
                    "manual determina expressamente que esse vício NÃO se usa "
                    "mais na contestação (regra 3.3).",
                    primeiro_trecho(minuta.texto, r"\b(CREA|CRM)\b"),
                )
            ]
        return [
            Resultado(
                self.id, self.bloco, self.descricao, Status.OK,
                "Sem menção ao vício obsoleto de registro no CREA/CRM.",
                None,
            )
        ]


# ---------------------------------------------------------------------------
# 3.17 — Vedação à conversão de tempo especial após 13/11/2019 (EC 103/2019)
# ---------------------------------------------------------------------------

_MARCO_EC103 = date(2019, 11, 13)
_PADROES_VEDACAO = ["vedada a conversao", "vedacao a conversao"]


@registrar
class VedacaoConversaoPos2019(Regra):
    id = "3.17-vedacao-conversao"
    bloco = BLOCO
    descricao = "Vedação à conversão (EC 103/2019) quando o período passa de 13/11/2019"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        datas_fim = [
            _data(p["fim"]) for p in minuta.periodos if _data(p["fim"])
        ]
        if not datas_fim:
            return []
        passa_do_marco = [d for d in datas_fim if d > _MARCO_EC103]
        norm = normalizar(minuta.texto)
        tem_vedacao = any(p in norm for p in _PADROES_VEDACAO)

        if passa_do_marco and not tem_vedacao:
            ultrapassa = max(passa_do_marco).strftime("%d/%m/%Y")
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.ERRO,
                    "Há período que ultrapassa 13/11/2019 (vai até "
                    f"{ultrapassa}), mas a minuta NÃO contém a vedação à "
                    "conversão de tempo especial em comum (Art. 25, §2º, EC "
                    "103/2019 — regra 3.17).",
                    None,
                )
            ]
        if passa_do_marco and tem_vedacao:
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.OK,
                    "Período ultrapassa 13/11/2019 e a vedação à conversão está "
                    "presente.",
                    None,
                )
            ]
        # nenhum período passa do marco: a presença da vedação é fundamento
        # padrão tolerado (não é erro); a ausência é o esperado.
        return [
            Resultado(
                self.id, self.bloco, self.descricao, Status.OK,
                "Nenhum período ultrapassa 13/11/2019; vedação não exigida.",
                None,
            )
        ]


# ---------------------------------------------------------------------------
# 3.1 — Consistência interna: períodos da síntese × tabela do mérito
# ---------------------------------------------------------------------------

_RE_PAR_DATAS = re.compile(
    r"de\s+(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})"
)


@registrar
class ConsistenciaSinteseTabela(Regra):
    """A síntese da demanda enumera os períodos requeridos; a tabela do mérito
    deve conter exatamente esses períodos. Divergência é inconsistência
    interna da minuta (impugnar período não pedido / omitir período pedido).
    A checagem contra a petição inicial em si, externa, fica para o LLM."""

    id = "3.1-consistencia-sintese-tabela"
    bloco = BLOCO
    descricao = "Períodos da tabela idênticos aos enumerados na síntese da demanda"

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        sintese = normalizar(minuta.secao("sintese"))
        pares_sintese = set(_RE_PAR_DATAS.findall(sintese))
        pares_tabela = {(p["inicio"], p["fim"]) for p in minuta.periodos}
        if not pares_sintese or not pares_tabela:
            return []  # sem enumeração comparável; nada a validar

        omitidos = pares_sintese - pares_tabela
        nao_pedidos = pares_tabela - pares_sintese
        if not omitidos and not nao_pedidos:
            return [
                Resultado(
                    self.id, self.bloco, self.descricao, Status.OK,
                    "Períodos da tabela conferem com os enumerados na síntese.",
                    None,
                )
            ]

        resultados: list[Resultado] = []
        if omitidos:
            lista = "; ".join(f"{a} a {b}" for a, b in sorted(omitidos))
            resultados.append(
                Resultado(
                    f"{self.id}:omitidos", self.bloco, self.descricao,
                    Status.ERRO,
                    "Período(s) requerido(s) na síntese da demanda e AUSENTE(s) "
                    f"da tabela de agentes nocivos: {lista} (regras 1.4/3.1: não "
                    "deixar de impugnar período requerido).",
                    None,
                )
            )
        if nao_pedidos:
            lista = "; ".join(f"{a} a {b}" for a, b in sorted(nao_pedidos))
            resultados.append(
                Resultado(
                    f"{self.id}:nao-pedidos", self.bloco, self.descricao,
                    Status.ERRO,
                    "Período(s) impugnado(s) na tabela que NÃO constam da síntese "
                    f"da demanda: {lista} (regras 1.4/3.1: não impugnar período "
                    "que o autor não requereu).",
                    None,
                )
            )
        return resultados
