"""Interface comum de regra e registro (registry) de regras.

Toda verificação — determinística (esta fase) ou futura (baseada em LLM) —
implementa a mesma interface ``Regra``. Isso permite que a fase do LLM seja
plugada sem alterar o orquestrador: basta registrar novas regras.

Uso:
    @registrar
    class MinhaRegra(Regra):
        id = "1.1-...";  bloco = "Bloco 1 - Estrutural"
        descricao = "..."
        def verificar(self, minuta): ...

O orquestrador (verificador.py) importa os módulos de regras, o que dispara o
registro, e depois itera sobre ``coletar_regras()``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..report import Resultado
from ..segmenter import Minuta

# registro global de regras determinísticas (preenchido pelo decorador)
_REGISTRO: list[type["Regra"]] = []


class Regra(ABC):
    """Interface comum a todas as regras de verificação.

    Atributos de classe (devem ser definidos pelas subclasses):
      - id: identificador estável (ex.: "1.3-marcacoes-edicao").
      - bloco: rótulo do bloco para agrupamento no relatório.
      - descricao: o que a regra checa.

    Subclasses determinísticas implementam ``verificar``. As regras da futura
    fase de LLM (ver ``llm_stubs.py``) seguem exatamente esta mesma interface.
    """

    id: str = ""
    bloco: str = ""
    descricao: str = ""

    # quando True, a regra depende de raciocínio/contexto e fica para a fase
    # do LLM; o orquestrador determinístico a ignora.
    requer_llm: bool = False

    @abstractmethod
    def verificar(self, minuta: Minuta) -> list[Resultado]:
        """Aplica a regra à minuta e devolve uma lista de resultados."""
        raise NotImplementedError


def registrar(cls: type[Regra]) -> type[Regra]:
    """Decorador que registra uma regra determinística no registro global."""
    _REGISTRO.append(cls)
    return cls


def coletar_regras() -> list[Regra]:
    """Instancia e devolve todas as regras determinísticas registradas."""
    return [cls() for cls in _REGISTRO]
