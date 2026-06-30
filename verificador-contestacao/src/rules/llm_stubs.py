"""Pontos de extensão para a FASE DO LLM (não implementados nesta fase).

Estas verificações exigem raciocínio contextual (datas, marcos temporais,
compatibilidade tese↔agente↔período, leitura da petição inicial) e por isso
NÃO são implementadas na camada determinística. Ficam aqui como stubs que
seguem a mesma interface ``Regra``, prontos para serem implementados e
registrados quando a camada de LLM for adicionada.

IMPORTANTE: estes stubs NÃO são registrados no registry determinístico — eles
não rodam na Fase 1. ``verificar`` levanta ``NotImplementedError`` de propósito.
O orquestrador pode listá-los (``stubs_llm()``) para informar ao usuário o que
ficou pendente para a próxima fase.
"""

from __future__ import annotations

from ..report import Resultado
from ..segmenter import Minuta
from . import Regra


class _StubLLM(Regra):
    """Base dos stubs: marca ``requer_llm`` e bloqueia execução determinística."""

    requer_llm = True

    def verificar(self, minuta: Minuta) -> list[Resultado]:
        raise NotImplementedError(
            f"Regra '{self.id}' depende da camada de LLM (Fase 2)."
        )


class CompatibilidadeTeseAgentePeriodo(_StubLLM):
    """Bloco 3 — Compatibilidade entre tese, período e agente nocivo.

    Deve avaliar os marcos temporais de cada agente (ruído, calor, biológico,
    etc.) e decidir se a tese declarada cobre corretamente o período — inclusive
    quando o período cruza uma fronteira temporal (ex.: ruído na fronteira de
    03/12/1998). Corresponde ao "Erro 2" do gabarito de teste.
    """

    id = "3.x-compat-tese-agente-periodo"
    bloco = "Bloco 3 - Agentes nocivos (LLM)"
    descricao = "Compatibilidade tese × agente × período (marcos temporais)"


class SituacoesPPPNaoApresentado(_StubLLM):
    """Bloco 2.8 — Distinção entre as três situações de PPP não apresentado.

    (1) PPP inexiste em qualquer lugar; (2) PPP só em juízo; (3) PPP judicial
    divergente do administrativo. A distinção exige ler o PA/dossiê.
    """

    id = "2.8-situacoes-ppp"
    bloco = "Bloco 2 - Preliminares (LLM)"
    descricao = "Distinção entre as três situações de PPP não apresentado"


class DecadenciaPrescricaoPorDatas(_StubLLM):
    """Bloco 2.4/2.5 — Lógica condicional de decadência/prescrição por datas.

    Deve decidir, a partir de DER, primeira prestação, data de ajuizamento e
    tipo de ação (concessão x revisão), se a preliminar é cabível. Corresponde
    ao "Erro 5" (decadência em ação de concessão) e ao "Erro 4" (prescrição
    ausente) do gabarito de teste.
    """

    id = "2.45-decadencia-prescricao-datas"
    bloco = "Bloco 2 - Preliminares (LLM)"
    descricao = "Cabimento de decadência/prescrição com base em datas e tipo de ação"


class CoberturaPeriodosInicial(_StubLLM):
    """Bloco 1.4 / 3.1 — Cobertura dos períodos requeridos na petição inicial.

    Exige ler a petição inicial (não está na minuta) para confirmar que todos
    os períodos requeridos estão na tabela e que nenhum período não requerido
    foi incluído.
    """

    id = "1.4-cobertura-periodos-inicial"
    bloco = "Bloco 1 - Estrutural (LLM)"
    descricao = "Cobertura dos períodos requeridos na petição inicial"


def stubs_llm() -> list[Regra]:
    """Lista os stubs da fase do LLM (para fins informativos no relatório)."""
    return [
        CompatibilidadeTeseAgentePeriodo(),
        SituacoesPPPNaoApresentado(),
        DecadenciaPrescricaoPorDatas(),
        CoberturaPeriodosInicial(),
    ]
