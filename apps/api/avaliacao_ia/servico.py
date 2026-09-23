"""Orquestra o lote da etapa 2. O código do cliente só roda para elegível com resposta."""

from __future__ import annotations

from typing import Any, Callable

import config
from avaliacao_ia.cliente import ClienteLLM, ErroClienteLLM, cliente_padrao
from avaliacao_ia.compatibilidade import calcular_compatibilidade
from avaliacao_ia.prompt import (
    INSTRUCOES_TECNICAS,
    MSG_CRITERIOS_DESALINHADOS,
    interpolar,
    texto_preview,
)
from avaliacao_ia.resposta import resposta_utilizavel
from avaliacao_ia.validacao import ErroValidacaoJson, validar_saida_modelo

MSG_CONFIG_AUSENTE = (
    "A avaliação por IA não está configurada. Defina as variáveis de ambiente do modelo "
    "(a chave não aparece nesta tela)."
)
MSG_SEM_MAPEAMENTO = (
    "Mapeie ao menos uma coluna de resposta do chatbot na importação. "
    "Sem esse mapeamento a avaliação por IA não roda."
)
MSG_SEM_CRITERIOS = "Cadastre ao menos um critério qualitativo da vaga."
MSG_SEM_PROMPT = "Salve um prompt do projeto antes de avaliar."
MSG_N_ZERO = "Nenhum candidato elegível com resposta utilizável está selecionado para envio."
FRASE_REPARO = (
    "Corrija para o schema exigido. Responda somente com o objeto JSON. "
    "Não invente fatos fora das respostas originais."
)


class RecusaLote(ValueError):
    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem


def recusar_se_nao_configurado() -> None:
    if not config.llm_configurada():
        raise RecusaLote(MSG_CONFIG_AUSENTE)


def _mensagens(template: str, candidato_id: str, itens: list[dict], respostas: list[dict]) -> list[dict[str, str]]:
    user = interpolar(template, candidato_id, itens, respostas)
    return [
        {"role": "system", "content": INSTRUCOES_TECNICAS},
        {"role": "user", "content": user},
    ]


def montar_preview(
    template: str,
    candidato_id: str,
    itens: list[dict],
    respostas: list[dict],
) -> str:
    return texto_preview(template, candidato_id, itens, respostas)


def _pode_enviar(decisao: dict | None, candidato: dict) -> bool:
    if not decisao or decisao.get("resultado") != "elegivel":
        return False
    return resposta_utilizavel(candidato.get("respostasChatbot"))


def avaliar_lote(
    *,
    candidatos_por_id: dict[str, dict],
    decisoes_por_id: dict[str, dict],
    ids_selecionados: list[str],
    template: str,
    prompt_id: str,
    criterios_prompt_versao_id: str,
    criterios_vigente_id: str,
    itens_embutidos: list[dict],
    mapeamento: dict | None,
    cliente: ClienteLLM | None = None,
    obter_cliente: Callable[[], ClienteLLM] | None = None,
) -> dict[str, Any]:
    recusar_se_nao_configurado()
    respostas_mapeadas = (mapeamento or {}).get("respostasChatbot") or []
    if not respostas_mapeadas:
        raise RecusaLote(MSG_SEM_MAPEAMENTO)
    if not itens_embutidos:
        raise RecusaLote(MSG_SEM_CRITERIOS)
    if not template.strip():
        raise RecusaLote(MSG_SEM_PROMPT)
    if criterios_prompt_versao_id != criterios_vigente_id:
        raise RecusaLote(MSG_CRITERIOS_DESALINHADOS)

    a_enviar = [
        cid
        for cid in ids_selecionados
        if _pode_enviar(decisoes_por_id.get(cid), candidatos_por_id.get(cid) or {})
    ]
    if not a_enviar:
        raise RecusaLote(MSG_N_ZERO)

    factory = obter_cliente or (lambda: cliente or cliente_padrao())
    cli = factory()
    resultados: list[dict[str, Any]] = []
    for cid in a_enviar:
        cand = candidatos_por_id[cid]
        resultado = _avaliar_um(
            cli,
            cand,
            template,
            prompt_id,
            criterios_prompt_versao_id,
            itens_embutidos,
        )
        resultados.append(resultado)
        if (resultado.get("erro") or {}).get("codigo") == "sem_credito":
            for restante in a_enviar[len(resultados) :]:
                copia = dict(resultado)
                copia["candidatoId"] = restante
                resultados.append(copia)
            break
    return {"enviados": a_enviar, "resultados": resultados}


def _uso_de(resposta: dict) -> dict:
    return resposta.get("uso") or {
        "entrada": None,
        "saida": None,
        "total": None,
        "nota": "uso_nao_reportado",
    }


def _avaliar_um(
    cli: ClienteLLM,
    candidato: dict,
    template: str,
    prompt_id: str,
    criterios_versao_id: str,
    itens: list[dict],
) -> dict[str, Any]:
    cid = candidato["candidatoId"]
    respostas = candidato.get("respostasChatbot") or []
    mensagens = _mensagens(template, cid, itens, respostas)
    tentativas_rede = 0
    houve_reparo = False
    uso = {"entrada": None, "saida": None, "total": None, "nota": "uso_nao_reportado"}
    try:
        primeira = cli.completar(mensagens)
        tentativas_rede = int(primeira.get("tentativasRede") or 1)
        uso = _uso_de(primeira)
        try:
            validado = validar_saida_modelo(primeira.get("conteudo") or "", itens, respostas)
        except ErroValidacaoJson as erro_json:
            houve_reparo = True
            json_rejeitado = primeira.get("conteudo") or ""
            reparo_msgs = mensagens + [
                {"role": "assistant", "content": json_rejeitado},
                {
                    "role": "user",
                    "content": f"{FRASE_REPARO} Motivo da rejeição: {erro_json.mensagem}",
                },
            ]
            segunda = cli.completar(reparo_msgs)
            tentativas_rede += int(segunda.get("tentativasRede") or 1)
            uso = _uso_de(segunda)
            try:
                validado = validar_saida_modelo(segunda.get("conteudo") or "", itens, respostas)
            except ErroValidacaoJson as erro_reparo:
                return _falha(
                    cid,
                    prompt_id,
                    criterios_versao_id,
                    erro_reparo.codigo,
                    tentativas_rede,
                    houve_reparo,
                    uso,
                )
    except ErroClienteLLM as erro:
        falha = _falha(cid, prompt_id, criterios_versao_id, erro.codigo, tentativas_rede or 1, houve_reparo, uso)
        if erro.mensagem:
            falha["erro"]["mensagem"] = erro.mensagem
        return falha

    calculada = calcular_compatibilidade(validado["justificativasPorCriterio"], itens)
    return {
        "candidatoId": cid,
        "promptVersionId": prompt_id,
        "criteriosQualitativosVersaoId": criterios_versao_id,
        "perfil": validado["perfil"],
        "compatibilidade": calculada,
        "compatibilidadeModelo": validado["compatibilidadeModelo"],
        "justificativasPorCriterio": validado["justificativasPorCriterio"],
        "usoToken": {
            "entrada": uso.get("entrada"),
            "saida": uso.get("saida"),
            "total": uso.get("total"),
        },
        "notaUso": uso.get("nota"),
        "estado": "sucesso",
        "erro": None,
        "tentativasRede": tentativas_rede,
        "houveReparoJson": houve_reparo,
        "statusChamada": "sucesso",
    }


def _falha(
    cid: str,
    prompt_id: str,
    criterios_versao_id: str,
    codigo: str,
    tentativas: int,
    houve_reparo: bool,
    uso: dict,
) -> dict[str, Any]:
    return {
        "candidatoId": cid,
        "promptVersionId": prompt_id,
        "criteriosQualitativosVersaoId": criterios_versao_id,
        "perfil": None,
        "compatibilidade": None,
        "compatibilidadeModelo": None,
        "justificativasPorCriterio": None,
        "usoToken": {
            "entrada": uso.get("entrada"),
            "saida": uso.get("saida"),
            "total": uso.get("total"),
        },
        "notaUso": uso.get("nota"),
        "estado": "falha_avaliacao",
        "erro": {"codigo": codigo, "mensagem": _mensagem_erro(codigo)},
        "tentativasRede": tentativas,
        "houveReparoJson": houve_reparo,
        "statusChamada": codigo,
    }


def _mensagem_erro(codigo: str) -> str:
    mapa = {
        "json_invalido": "A resposta do modelo não passou na validação após o reparo.",
        "trecho_nao_encontrado": "O trecho citado não aparece nas respostas enviadas.",
        "justificativa_sem_trecho": "A justificativa não cita o trecho correspondente.",
        "timeout": "A chamada ao modelo esgotou o tempo limite.",
        "falha_rede": "Falha de rede ao chamar o modelo.",
        "sem_credito": "A conta do modelo está sem cota ou sem créditos. Troque a chave ou recarregue o saldo para avaliar.",
        "erro_http": "O provedor recusou a chamada.",
        "config_ausente": MSG_CONFIG_AUSENTE,
    }
    return mapa.get(codigo, "Falha de avaliação.")
