"""Utilitários de texto.

Funções auxiliares de normalização e busca, usadas por extrator, segmentador
e regras. A normalização sem acentos torna as verificações robustas a
variações de codificação na extração de PDF e a pequenas diferenças de grafia.
"""

import re
import unicodedata


def normalizar(texto: str) -> str:
    """Devolve o texto em minúsculas, sem acentos e com espaços colapsados.

    Útil para comparações tolerantes: "Decadência", "DECADENCIA" e
    "decadencia" passam a ser equivalentes.
    """
    if not texto:
        return ""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = sem_acento.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def contem(texto: str, termo: str) -> bool:
    """Verdadeiro se ``termo`` aparece em ``texto`` ignorando acentos e caixa."""
    return normalizar(termo) in normalizar(texto)


def contem_regex(texto: str, padrao: str) -> bool:
    """Verdadeiro se o ``padrao`` (regex) casa no texto normalizado."""
    return re.search(padrao, normalizar(texto)) is not None


def primeiro_trecho(texto: str, padrao: str, contexto: int = 60) -> str | None:
    """Devolve o primeiro trecho do texto ORIGINAL que casa com ``padrao``.

    O casamento é feito sobre o texto original (preservando acentos e caixa),
    com um pouco de contexto ao redor para servir de evidência no relatório.
    Retorna ``None`` se não houver casamento.
    """
    m = re.search(padrao, texto, flags=re.IGNORECASE)
    if not m:
        return None
    ini = max(0, m.start() - contexto)
    fim = min(len(texto), m.end() + contexto)
    trecho = texto[ini:fim].strip()
    trecho = re.sub(r"\s+", " ", trecho)
    prefixo = "..." if ini > 0 else ""
    sufixo = "..." if fim < len(texto) else ""
    return f"{prefixo}{trecho}{sufixo}"
