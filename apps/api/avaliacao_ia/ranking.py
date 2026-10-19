"""Média, zeramento técnico e posições do lote. A posição não vem do modelo."""

from __future__ import annotations


def media_meio_para_cima(nota_tecnica: int, nota_comportamental: int) -> int:
    """Média inteira em que 0,5 sobe. round() do Python manda 0,5 para o par."""
    return (nota_tecnica + nota_comportamental + 1) // 2


def _toda_sem_informacao(por_pergunta: list) -> bool:
    if not por_pergunta:
        return False
    return all(isinstance(item, dict) and item.get("resultado") == "sem_informacao" for item in por_pergunta)


def notas_para_gravar(nota_tecnica: int, nota_comportamental: int, por_pergunta: list) -> dict:
    """Zera a técnica antes da média quando toda pergunta da chamada é sem_informacao."""
    zerada = _toda_sem_informacao(por_pergunta)
    tecnica = 0 if zerada else nota_tecnica
    return {
        "notaTecnica": tecnica,
        "notaComportamental": nota_comportamental,
        "notaFinal": media_meio_para_cima(tecnica, nota_comportamental),
        "notaTecnicaZeradaPorFaltaDeInformacao": zerada,
    }


def atribuir_posicoes(entradas: list[dict]) -> dict[str, dict[str, int]]:
    """Ordem total: 1, 2, 3, sem pular e sem duas pessoas na mesma posição."""
    destino: dict[str, dict[str, int]] = {item["candidatoId"]: {} for item in entradas}

    def marcar(ordenados: list[dict], campo: str) -> None:
        for indice, item in enumerate(ordenados, start=1):
            destino[item["candidatoId"]][campo] = indice

    marcar(
        sorted(entradas, key=lambda item: (-item["notaTecnica"], -item["notaComportamental"], item["linhaOrigem"])),
        "posicaoTecnica",
    )
    marcar(
        sorted(entradas, key=lambda item: (-item["notaComportamental"], -item["notaTecnica"], item["linhaOrigem"])),
        "posicaoComportamental",
    )
    marcar(
        sorted(entradas, key=lambda item: (-item["notaFinal"], -item["notaTecnica"], item["linhaOrigem"])),
        "posicaoFinal",
    )
    return destino
