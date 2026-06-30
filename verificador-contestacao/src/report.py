"""Modelo de resultado das verificações e serialização (JSON e terminal).

Define o ``Resultado`` (uma verificação executada), o ``Relatorio`` (conjunto
de resultados + veredito) e funções para serializar em JSON e para imprimir
uma versão legível no terminal.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum


class Status(str, Enum):
    """Status possível de uma verificação."""

    OK = "OK"
    ERRO = "ERRO"
    VERIFICAR = "VERIFICAR"
    INFO = "INFO"


@dataclass
class Resultado:
    """Resultado de uma única verificação.

    Campos:
      - id: identificador estável da verificação (ex.: "1.1-enderecamento").
      - bloco: bloco da especificação a que pertence (ex.: "Bloco 1 - Estrutural").
      - descricao: o que a verificação checa.
      - status: OK | ERRO | VERIFICAR | INFO.
      - mensagem: explicação legível do resultado.
      - evidencia: trecho do texto (com seção/posição quando possível) que
        embasou a conclusão; pode ser None quando não houver.
    """

    id: str
    bloco: str
    descricao: str
    status: Status
    mensagem: str
    evidencia: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class Relatorio:
    """Conjunto de resultados + veredito final."""

    resultados: list[Resultado] = field(default_factory=list)

    def adicionar(self, resultado: Resultado) -> None:
        self.resultados.append(resultado)

    def estender(self, resultados: list[Resultado]) -> None:
        self.resultados.extend(resultados)

    @property
    def erros(self) -> list[Resultado]:
        return [r for r in self.resultados if r.status == Status.ERRO]

    @property
    def verificar(self) -> list[Resultado]:
        return [r for r in self.resultados if r.status == Status.VERIFICAR]

    @property
    def veredito(self) -> str:
        """REPROVADO se houver qualquer ERRO; caso contrário APROVADO."""
        return "REPROVADO" if self.erros else "APROVADO"

    # ---- serialização -----------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "veredito": self.veredito,
            "total_erros": len(self.erros),
            "total_verificar": len(self.verificar),
            "verificacoes": [r.to_dict() for r in self.resultados],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# --------------------------------------------------------------------------
# Renderização para o terminal
# --------------------------------------------------------------------------

_SIMBOLOS = {
    Status.OK: "[OK]",
    Status.ERRO: "[ERRO]",
    Status.VERIFICAR: "[VERIFICAR]",
    Status.INFO: "[INFO]",
}


def render_terminal(relatorio: Relatorio, usar_cor: bool = False) -> str:
    """Devolve a versão legível do relatório, agrupada por bloco."""
    linhas: list[str] = []
    veredito = relatorio.veredito
    linhas.append("=" * 70)
    linhas.append(f"  VEREDITO: {veredito}")
    linhas.append(
        f"  Erros: {len(relatorio.erros)}   |   "
        f"Pontos de verificação manual: {len(relatorio.verificar)}"
    )
    linhas.append("=" * 70)

    # agrupar por bloco preservando a ordem de aparição
    blocos: dict[str, list[Resultado]] = {}
    for r in relatorio.resultados:
        blocos.setdefault(r.bloco, []).append(r)

    for bloco, itens in blocos.items():
        linhas.append("")
        linhas.append(f"### {bloco}")
        for r in itens:
            simbolo = _SIMBOLOS[r.status]
            linhas.append(f"  {simbolo} {r.descricao}")
            linhas.append(f"      {r.mensagem}")
            if r.evidencia:
                linhas.append(f"      evidência: {r.evidencia}")

    if relatorio.verificar:
        linhas.append("")
        linhas.append("-" * 70)
        linhas.append("  PENDÊNCIAS DE VERIFICAÇÃO MANUAL:")
        for r in relatorio.verificar:
            linhas.append(f"   - {r.descricao}: {r.mensagem}")

    linhas.append("")
    return "\n".join(linhas)
