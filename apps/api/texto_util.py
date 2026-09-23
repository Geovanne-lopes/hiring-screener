"""Utilitário de texto compartilhado. Sem regra de cargo/idade e sem HTTP."""

from __future__ import annotations

import re
import unicodedata

_WS = re.compile(r"\s+", re.UNICODE)


def para_string(valor: object) -> str:
    if valor is None:
        return ""
    return str(valor)


def colapsar_espacos(texto: str) -> str:
    return _WS.sub(" ", texto.strip())


def texto_apos_strip_e_espaco(valor: object) -> str:
    return colapsar_espacos(para_string(valor))


def normalizar(valor: object) -> str:
    """Trim, colapso de espaço, NFKD sem marcas, casefold. Sem sinônimo nem primeira palavra."""
    texto = texto_apos_strip_e_espaco(valor)
    decomposto = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(ch for ch in decomposto if not unicodedata.combining(ch))
    return sem_acento.casefold()
