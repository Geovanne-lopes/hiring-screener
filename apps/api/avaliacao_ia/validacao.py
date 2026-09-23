from __future__ import annotations

import json
from typing import Any

from texto_util import colapsar_espacos, texto_apos_strip_e_espaco

from avaliacao_ia.prompt import formatar_respostas

RESULTADOS_OK = {"atende", "atende_parcialmente", "nao_atende", "sem_informacao"}
COMPAT_MODELO = {"compativel", "parcial", "incompativel"}


class ErroValidacaoJson(ValueError):
    def __init__(self, codigo: str, mensagem: str) -> None:
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


def _sem_cerca(texto: str) -> str:
    linhas = texto.splitlines()
    if linhas and linhas[0].lstrip().startswith("```"):
        linhas = linhas[1:]
    if linhas and linhas[-1].strip().startswith("```"):
        linhas = linhas[:-1]
    return "\n".join(linhas).strip()


def _parse_objeto(corpo: str) -> dict[str, Any]:
    texto = _sem_cerca((corpo or "").strip())
    if not texto:
        raise ErroValidacaoJson("json_invalido", "Resposta vazia.")
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError:
        inicio = texto.find("{")
        fim = texto.rfind("}")
        recorte = texto[inicio : fim + 1] if inicio >= 0 and fim > inicio else ""
        try:
            dados = json.loads(recorte) if recorte else None
        except json.JSONDecodeError as exc:
            raise ErroValidacaoJson("json_invalido", "Corpo não é JSON válido.") from exc
        if dados is None:
            raise ErroValidacaoJson("json_invalido", "Corpo não é JSON válido.")
    if not isinstance(dados, dict):
        raise ErroValidacaoJson("json_invalido", "JSON não é um objeto.")
    return dados


def _substring_colapsada(agulha: str, palheiro: str) -> bool:
    a = colapsar_espacos(agulha)
    p = colapsar_espacos(palheiro)
    return a in p if a else False


def validar_saida_modelo(
    corpo: str,
    itens_embutidos: list[dict],
    respostas: list[dict],
) -> dict[str, Any]:
    dados = _parse_objeto(corpo)
    for chave in ("perfil", "compatibilidade", "por_criterio", "trechos"):
        if chave not in dados:
            raise ErroValidacaoJson("json_invalido", f"Falta a chave {chave}.")

    perfil = texto_apos_strip_e_espaco(dados.get("perfil"))
    if not perfil or len(perfil) > 2000:
        raise ErroValidacaoJson("json_invalido", "perfil vazio ou acima de 2000 caracteres.")

    compat = dados.get("compatibilidade")
    if compat not in COMPAT_MODELO:
        raise ErroValidacaoJson("json_invalido", "compatibilidade do modelo inválida.")

    por_criterio = dados.get("por_criterio")
    trechos = dados.get("trechos")
    if not isinstance(por_criterio, list) or not isinstance(trechos, list):
        raise ErroValidacaoJson("json_invalido", "por_criterio e trechos devem ser listas.")

    ordenados = sorted(itens_embutidos, key=lambda x: int(x.get("ordem") or 0))
    if len(por_criterio) != len(ordenados) or len(trechos) != len(ordenados):
        raise ErroValidacaoJson("json_invalido", "por_criterio não corresponde aos critérios configurados.")

    ids_esperados = [i["criterioId"] for i in ordenados]
    nomes = {i["criterioId"]: i["nome"] for i in ordenados}
    enviado = formatar_respostas(respostas)

    justificativas: list[dict] = []
    for esperado, julgamento, trecho_item in zip(ordenados, por_criterio, trechos, strict=True):
        if not isinstance(julgamento, dict) or not isinstance(trecho_item, dict):
            raise ErroValidacaoJson("json_invalido", "Item de por_criterio ou trechos inválido.")
        cid = julgamento.get("criterioId")
        if cid != esperado["criterioId"] or trecho_item.get("criterioId") != cid:
            raise ErroValidacaoJson(
                "json_invalido",
                "criterioId desconhecido ou fora de ordem. "
                f"Use exatamente {esperado['criterioId']} para {esperado['nome']}.",
            )
        if cid not in ids_esperados:
            raise ErroValidacaoJson("json_invalido", "criterioId desconhecido.")
        if julgamento.get("nome") != nomes[cid] or trecho_item.get("nome") != nomes[cid]:
            raise ErroValidacaoJson("json_invalido", "nome do critério não coincide com a versão.")
        resultado = julgamento.get("resultado")
        if resultado not in RESULTADOS_OK:
            raise ErroValidacaoJson("json_invalido", "resultado inválido.")
        trecho = trecho_item.get("trecho")
        if trecho is None:
            trecho = ""
        if not isinstance(trecho, str):
            raise ErroValidacaoJson("json_invalido", "trecho inválido.")
        justificativa = julgamento.get("justificativa") or ""
        if resultado == "sem_informacao":
            if trecho != "":
                raise ErroValidacaoJson("json_invalido", "sem_informacao exige trecho vazio.")
        else:
            if texto_apos_strip_e_espaco(trecho) == "":
                raise ErroValidacaoJson("json_invalido", "trecho obrigatório quando há julgamento informado.")
            if not _substring_colapsada(trecho, enviado):
                raise ErroValidacaoJson("trecho_nao_encontrado", "Trecho não aparece nas respostas enviadas.")
            if not isinstance(justificativa, str):
                justificativa = str(justificativa)
            if not _substring_colapsada(trecho, justificativa):
                justificativa = f"{justificativa} {trecho}".strip()
        justificativas.append(
            {
                "criterioId": cid,
                "nome": nomes[cid],
                "resultado": resultado,
                "justificativa": justificativa,
                "trecho": trecho,
            }
        )

    return {
        "perfil": perfil,
        "compatibilidadeModelo": compat,
        "por_criterio": por_criterio,
        "justificativasPorCriterio": justificativas,
    }
