from __future__ import annotations

INFORMADOS = {"atende", "atende_parcialmente", "nao_atende"}


def calcular_compatibilidade(por_criterio: list[dict], itens_embutidos: list[dict]) -> str:
    por_id = {item["criterioId"]: item for item in itens_embutidos}
    for julgamento in por_criterio:
        item = por_id.get(julgamento["criterioId"]) or {}
        if item.get("eliminatorio") and julgamento.get("resultado") == "nao_atende":
            return "incompativel"
    informados = [j for j in por_criterio if j.get("resultado") in INFORMADOS]
    if informados and all(j.get("resultado") == "nao_atende" for j in informados):
        return "incompativel"
    if por_criterio and all(j.get("resultado") == "atende" for j in por_criterio):
        return "compativel"
    return "parcial"
