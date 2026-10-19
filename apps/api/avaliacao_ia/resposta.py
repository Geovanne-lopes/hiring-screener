"""Resposta de chatbot utilizável. A pergunta é o cabeçalho da coluna."""

from __future__ import annotations

from texto_util import para_string, texto_apos_strip_e_espaco


def pares_da_linha(respostas: list | None) -> list[dict]:
    """Pares utilizáveis. O id segue a ordem do mapeamento, inclusive se uma célula vazia fica de fora."""
    pares = []
    for indice, item in enumerate(respostas or [], start=1):
        bruto = item or {}
        texto = para_string(bruto.get("texto"))
        if texto_apos_strip_e_espaco(texto) == "":
            continue
        pares.append(
            {
                "perguntaId": f"p{indice}",
                "pergunta": para_string(bruto.get("colunaMapeada")).strip(),
                "texto": texto,
            }
        )
    return pares


def resposta_utilizavel(respostas: list | None) -> bool:
    return len(pares_da_linha(respostas)) > 0
