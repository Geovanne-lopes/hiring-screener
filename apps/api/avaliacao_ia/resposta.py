"""Resposta de chatbot utilizável. Não julga cargo, idade nem escolaridade."""

from __future__ import annotations

from texto_util import texto_apos_strip_e_espaco


def resposta_utilizavel(respostas: list | None) -> bool:
    for item in respostas or []:
        texto = texto_apos_strip_e_espaco((item or {}).get("texto"))
        if len(texto) > 0:
            return True
    return False


def respostas_utilizaveis(respostas: list | None) -> list[dict]:
    saida = []
    for item in respostas or []:
        texto = texto_apos_strip_e_espaco((item or {}).get("texto"))
        if texto:
            saida.append(
                {
                    "colunaMapeada": (item or {}).get("colunaMapeada") or "",
                    "texto": (item or {}).get("texto") or "",
                }
            )
    return saida
