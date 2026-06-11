"""
Módulo de utilitários.

Contém funções auxiliares usadas pelos demais módulos do sistema.
"""

import unicodedata


def normalize(texto: str) -> str:
    """
    Normaliza uma string removendo acentos, convertendo para ASCII,
    minúsculas e removendo espaços extras nas bordas.

    Args:
        texto: A string a ser normalizada.

    Returns:
        A string normalizada (ASCII, lowercase, sem acentos).
    """
    return unicodedata.normalize("NFKD", texto or "").encode("ASCII", "ignore").decode().lower().strip()