"""Único ponto de chamada externa ao LLM. Não recalcula triagem."""

from avaliacao_ia.compatibilidade import calcular_compatibilidade
from avaliacao_ia.prompt import (
    INSTRUCOES_TECNICAS,
    TEMPLATE_INICIAL,
    interpolar,
    texto_preview,
    validar_template,
)
from avaliacao_ia.resposta import resposta_utilizavel
from avaliacao_ia.servico import avaliar_lote, montar_preview, recusar_se_nao_configurado

__all__ = [
    "INSTRUCOES_TECNICAS",
    "TEMPLATE_INICIAL",
    "avaliar_lote",
    "calcular_compatibilidade",
    "interpolar",
    "montar_preview",
    "recusar_se_nao_configurado",
    "resposta_utilizavel",
    "texto_preview",
    "validar_template",
]
