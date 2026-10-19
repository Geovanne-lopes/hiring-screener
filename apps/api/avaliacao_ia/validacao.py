from __future__ import annotations

import json
from typing import Any

from texto_util import colapsar_espacos, texto_apos_strip_e_espaco

from avaliacao_ia.resposta import pares_da_linha

RESULTADOS_OK = {"atende", "atende_parcialmente", "nao_atende", "sem_informacao"}
CHAVES_OBJETO = {
    "perfil",
    "por_pergunta",
    "trechos",
    "nota_tecnica",
    "nota_comportamental",
    "justificativa_nota_tecnica",
    "justificativa_nota_comportamental",
}
FRASE_ZERAMENTO_TECNICO = (
    "A nota técnica foi zerada porque nenhuma resposta trouxe informação "
    "para cruzar com a pergunta e a job description."
)
CHAVES_PERGUNTA = {"perguntaId", "pergunta", "resultado", "justificativa"}
CHAVES_TRECHO = {"perguntaId", "trecho"}
ROTULO_SEM_INFORMACAO = "sem informação para julgar esta pergunta"


class ErroValidacaoJson(ValueError):
    def __init__(self, codigo: str, mensagem: str) -> None:
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


def rotulo_resultado(resultado: str) -> str:
    if resultado == "sem_informacao":
        return ROTULO_SEM_INFORMACAO
    return resultado


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


def _nota(valor: object, nome: str) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0 or valor > 100:
        raise ErroValidacaoJson("json_invalido", f"{nome} ausente ou fora de 0 a 100.")
    return valor


def _justificativa_nota(valor: object, nome: str) -> str:
    if not isinstance(valor, str) or texto_apos_strip_e_espaco(valor) == "":
        raise ErroValidacaoJson("json_invalido", f"{nome} ausente ou vazia.")
    return valor


def _objeto_json(texto: str) -> dict | None:
    bruto = texto.strip()
    if not bruto.startswith("{"):
        return None
    try:
        carregado = json.loads(bruto)
    except json.JSONDecodeError:
        return None
    return carregado if isinstance(carregado, dict) else None


def _objeto_da_lista(item: object, lista: str, indice: int) -> dict:
    if isinstance(item, dict):
        return item
    if isinstance(item, str):
        carregado = _objeto_json(item)
        if carregado is not None:
            return carregado
    if isinstance(item, list) and len(item) == 1 and isinstance(item[0], dict):
        return item[0]
    raise ErroValidacaoJson("json_invalido", f"Item {indice} de {lista} não é um objeto.")


def _objeto_trecho(item: object, julgamento: dict, pergunta_id: str, indice: int) -> dict:
    if isinstance(item, str) and _objeto_json(item) is None:
        return {"perguntaId": pergunta_id, "trecho": item}
    if item is None and isinstance(julgamento.get("trecho"), str):
        return {"perguntaId": pergunta_id, "trecho": julgamento["trecho"]}
    return _objeto_da_lista(item, "trechos", indice)


def validar_saida_modelo(corpo: str, respostas: list[dict]) -> dict[str, Any]:
    dados = _parse_objeto(corpo)
    chaves = set(dados.keys())
    if chaves != CHAVES_OBJETO:
        faltando = sorted(CHAVES_OBJETO - chaves)
        if faltando:
            raise ErroValidacaoJson("json_invalido", "Chave ausente: " + ", ".join(faltando) + ".")
        raise ErroValidacaoJson("json_invalido", "O JSON não tem exatamente as chaves exigidas.")

    perfil = dados.get("perfil")
    if not isinstance(perfil, str):
        raise ErroValidacaoJson("json_invalido", "perfil inválido.")

    por_pergunta = dados.get("por_pergunta")
    trechos = dados.get("trechos")
    if not isinstance(por_pergunta, list) or not isinstance(trechos, list):
        raise ErroValidacaoJson("json_invalido", "por_pergunta e trechos devem ser listas.")

    enviados = pares_da_linha(respostas)
    if len(por_pergunta) != len(enviados) or len(trechos) != len(enviados):
        raise ErroValidacaoJson("json_invalido", "A lista não corresponde às perguntas enviadas.")

    nota_tecnica = _nota(dados.get("nota_tecnica"), "nota_tecnica")
    nota_comportamental = _nota(dados.get("nota_comportamental"), "nota_comportamental")
    justificativa_nota_tecnica = _justificativa_nota(
        dados.get("justificativa_nota_tecnica"), "justificativa_nota_tecnica"
    )
    justificativa_nota_comportamental = _justificativa_nota(
        dados.get("justificativa_nota_comportamental"), "justificativa_nota_comportamental"
    )

    julgamentos: list[dict] = []
    trechos_ok: list[dict] = []
    for indice, (esperado, julgamento, trecho_item) in enumerate(
        zip(enviados, por_pergunta, trechos, strict=True), start=1
    ):
        julgamento = _objeto_da_lista(julgamento, "por_pergunta", indice)
        trecho_item = _objeto_trecho(trecho_item, julgamento, esperado["perguntaId"], indice)
        if not CHAVES_PERGUNTA <= set(julgamento.keys()) or not CHAVES_TRECHO <= set(trecho_item.keys()):
            raise ErroValidacaoJson("json_invalido", "Chave ausente no item da pergunta.")
        if julgamento.get("perguntaId") != esperado["perguntaId"] or trecho_item.get("perguntaId") != esperado["perguntaId"]:
            raise ErroValidacaoJson("json_invalido", "perguntaId trocado ou fora de ordem.")
        if julgamento.get("pergunta") != esperado["pergunta"]:
            raise ErroValidacaoJson("json_invalido", "A pergunta não coincide com o cabeçalho enviado.")
        resultado = julgamento.get("resultado")
        if resultado not in RESULTADOS_OK:
            raise ErroValidacaoJson("json_invalido", "resultado inválido.")
        justificativa = julgamento.get("justificativa")
        if not isinstance(justificativa, str) or texto_apos_strip_e_espaco(justificativa) == "":
            raise ErroValidacaoJson("json_invalido", "justificativa vazia.")
        trecho = trecho_item.get("trecho")
        if not isinstance(trecho, str):
            raise ErroValidacaoJson("json_invalido", "trecho inválido.")
        if resultado == "sem_informacao":
            if trecho != "":
                raise ErroValidacaoJson("json_invalido", "sem_informacao exige trecho vazio.")
        else:
            if texto_apos_strip_e_espaco(trecho) == "":
                raise ErroValidacaoJson("json_invalido", "trecho obrigatório quando há julgamento informado.")
            if not _substring_colapsada(trecho, esperado["texto"]):
                raise ErroValidacaoJson("trecho_nao_encontrado", "Trecho não aparece na resposta da pergunta.")
        julgamentos.append(
            {
                "perguntaId": esperado["perguntaId"],
                "pergunta": esperado["pergunta"],
                "resultado": resultado,
                "justificativa": justificativa,
            }
        )
        trechos_ok.append({"perguntaId": esperado["perguntaId"], "trecho": trecho})

    return {
        "perfil": perfil,
        "por_pergunta": julgamentos,
        "trechos": trechos_ok,
        "nota_tecnica": nota_tecnica,
        "nota_comportamental": nota_comportamental,
        "justificativa_nota_tecnica": justificativa_nota_tecnica,
        "justificativa_nota_comportamental": justificativa_nota_comportamental,
    }
