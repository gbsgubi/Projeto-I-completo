"""Orquestrador + interface de linha de comando (entry point).

Fluxo:
  1. Recebe o caminho de uma minuta (.pdf ou .html).
  2. Extrai e segmenta o texto.
  3. Aplica todas as regras determinísticas registradas.
  4. Emite o relatório (terminal e/ou JSON).

Uso:
    python -m src.verificador caminho/da/minuta.pdf
    python -m src.verificador minuta.html --json saida.json
"""

from __future__ import annotations

import argparse
import sys

from .extractor import extrair
from .report import Relatorio, render_terminal
from .segmenter import segmentar

# importar os módulos de regras dispara o registro no registry.
from .rules import coletar_regras
from .rules import estrutural as _estrutural  # noqa: F401
from .rules import preliminares as _preliminares  # noqa: F401
from .rules import redistribuicao as _redistribuicao  # noqa: F401
from .rules import teses as _teses  # noqa: F401
from .rules.llm_stubs import stubs_llm


def verificar_minuta(caminho: str) -> Relatorio:
    """Executa o pipeline completo sobre a minuta e devolve o ``Relatorio``."""
    documento = extrair(caminho)
    minuta = segmentar(documento)

    relatorio = Relatorio()
    for regra in coletar_regras():
        relatorio.estender(regra.verificar(minuta))
    return relatorio


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="verificador-contestacao",
        description="Verificação determinística (Fase 1) de minutas de contestação.",
    )
    p.add_argument("caminho", help="caminho da minuta (.pdf ou .html)")
    p.add_argument(
        "--json", metavar="ARQUIVO", default=None,
        help="grava o relatório JSON no arquivo indicado",
    )
    p.add_argument(
        "--so-json", action="store_true",
        help="imprime apenas o JSON no stdout (sem a versão de terminal)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        relatorio = verificar_minuta(args.caminho)
    except (FileNotFoundError, ValueError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 2

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            f.write(relatorio.to_json())

    if args.so_json:
        print(relatorio.to_json())
    else:
        print(render_terminal(relatorio))
        pendentes = stubs_llm()
        if pendentes:
            print("-" * 70)
            print("  VERIFICAÇÕES ADIADAS PARA A FASE DO LLM (não executadas):")
            for s in pendentes:
                print(f"   - [{s.id}] {s.descricao}")
            print("")

    # código de saída: 1 se REPROVADO, 0 se APROVADO (útil em automações)
    return 1 if relatorio.veredito == "REPROVADO" else 0


if __name__ == "__main__":
    raise SystemExit(main())
