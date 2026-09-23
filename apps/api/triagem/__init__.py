"""Módulo de triagem determinística: função pura, zero HTTP.

Não importa avaliacao_ia.
"""

from triagem.avaliar import (
    avaliar_candidato,
    criterios_iniciais,
    incluir_item_lista,
    mensagens_bloqueio_execucao,
)
from triagem.normalizacao import normalizar

__all__ = [
    "avaliar_candidato",
    "criterios_iniciais",
    "incluir_item_lista",
    "mensagens_bloqueio_execucao",
    "normalizar",
]
