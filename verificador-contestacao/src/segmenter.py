"""Segmentação da minuta em seções.

A partir do documento extraído, identifica as seções da minuta por
palavras-chave/títulos (ex.: "PRELIMINARES", "DO MÉRITO", "Período(s):",
"Fundamentos da defesa"), de forma robusta a pequenas variações. Produz um
objeto ``Minuta`` que é a entrada de todas as regras.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .extractor import DocumentoExtraido
from .utils import normalizar

# Títulos de seção esperados na minuta padrão (modelo 544316). A detecção é
# tolerante a numeração romana, acentos e caixa. Cada item é (chave, regex no
# texto JÁ normalizado sem acentos).
_TITULOS_SECAO = [
    ("sintese", r"sintese da demanda"),
    ("preliminares", r"\bpreliminares\b"),
    ("merito", r"do merito\b"),
    ("outros_fundamentos", r"outros fundamentos"),
    ("pedidos", r"dos pedidos\b"),
]


@dataclass
class Minuta:
    """Minuta segmentada — entrada das regras de verificação.

    Campos:
      - documento: o DocumentoExtraido de origem.
      - texto: texto plano completo.
      - secoes: mapeamento chave-de-seção -> conteúdo textual da seção.
      - periodos: lista de blocos de período/agente extraídos do mérito.
    """

    documento: DocumentoExtraido
    texto: str
    secoes: dict[str, str] = field(default_factory=dict)
    periodos: list[dict] = field(default_factory=list)

    # atalhos de conveniência ------------------------------------------------

    @property
    def formato(self) -> str:
        return self.documento.formato

    @property
    def destaques_amarelos(self) -> list[str]:
        return self.documento.destaques_amarelos

    @property
    def suporta_amarelo(self) -> bool:
        return self.documento.suporta_amarelo

    def secao(self, chave: str) -> str:
        """Conteúdo da seção (string vazia se ausente)."""
        return self.secoes.get(chave, "")


def segmentar(documento: DocumentoExtraido) -> Minuta:
    """Constrói a ``Minuta`` segmentada a partir do documento extraído."""
    texto = documento.texto
    secoes = _dividir_secoes(texto)
    periodos = _extrair_periodos(secoes.get("merito", texto))
    return Minuta(
        documento=documento,
        texto=texto,
        secoes=secoes,
        periodos=periodos,
    )


def _dividir_secoes(texto: str) -> dict[str, str]:
    """Divide o texto nas seções conhecidas, varrendo linha a linha.

    Estratégia robusta: percorre as linhas; quando uma linha (normalizada)
    casa com um dos títulos de seção, troca a seção corrente. O texto antes da
    primeira seção fica em "cabecalho".
    """
    linhas = texto.splitlines()
    secoes: dict[str, list[str]] = {"cabecalho": []}
    atual = "cabecalho"

    for linha in linhas:
        norm = normalizar(linha)
        nova = None
        # só considera título quando a linha é curta (evita casar no meio de
        # um parágrafo longo) ou começa com numeração de seção.
        if len(norm) <= 60:
            for chave, padrao in _TITULOS_SECAO:
                if re.search(padrao, norm):
                    nova = chave
                    break
        if nova:
            atual = nova
            secoes.setdefault(atual, [])
            secoes[atual].append(linha)
        else:
            secoes.setdefault(atual, [])
            secoes[atual].append(linha)

    return {chave: "\n".join(linhas) for chave, linhas in secoes.items()}


# Cabeçalho de bloco de período no mérito, ex.:
# "III.1 - Período de 06/03/1997 a 31/12/2002 - Agente: Ruído"
_RE_CABECALHO_PERIODO = re.compile(
    r"per[ií]odo de\s+(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})"
    r".*?agente[:\s]+([^\n\r]+)",
    re.IGNORECASE,
)


def _extrair_periodos(texto_merito: str) -> list[dict]:
    """Extrai blocos de período/agente do mérito.

    Cada bloco vira um dict com 'inicio', 'fim', 'agente' e 'texto' (o trecho
    de fundamentos daquele período). Útil para a futura fase de LLM e para a
    catalogação. Aqui é informativo e tolerante: se nada casar, retorna [].
    """
    periodos: list[dict] = []
    matches = list(_RE_CABECALHO_PERIODO.finditer(texto_merito))
    for i, m in enumerate(matches):
        ini_txt = m.end()
        fim_txt = matches[i + 1].start() if i + 1 < len(matches) else len(texto_merito)
        periodos.append(
            {
                "inicio": m.group(1),
                "fim": m.group(2),
                "agente": m.group(3).strip(),
                "texto": texto_merito[m.start():fim_txt].strip(),
            }
        )
    return periodos
