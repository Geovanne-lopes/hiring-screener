"""Gate da etapa 2: cliente LLM só para elegível com resposta; chave vazia recusa o lote."""

from __future__ import annotations

import pytest

from avaliacao_ia.compatibilidade import calcular_compatibilidade
from avaliacao_ia.servico import MSG_CONFIG_AUSENTE, RecusaLote, avaliar_lote


class ClienteEspiao:
    def __init__(self) -> None:
        self.chamadas = 0

    def completar(self, mensagens):
        self.chamadas += 1
        raise AssertionError("cliente não deveria ser chamado")


ITENS = [
    {
        "criterioId": "cq_01",
        "nome": "Disponibilidade de horário",
        "descricao": "Turnos",
        "ordem": 1,
        "eliminatorio": False,
    },
    {
        "criterioId": "cq_02",
        "nome": "Experiência relatada no atendimento",
        "descricao": "Atendimento",
        "ordem": 2,
        "eliminatorio": False,
    },
    {
        "criterioId": "cq_03",
        "nome": "Aderência ao tipo de atendimento",
        "descricao": "Tipo",
        "ordem": 3,
        "eliminatorio": True,
    },
]


def _kwargs(**extra):
    base = dict(
        candidatos_por_id={
            "ineleg": {
                "candidatoId": "ineleg",
                "respostasChatbot": [{"colunaMapeada": "R1", "texto": "texto longo o bastante"}],
            },
            "semresp": {"candidatoId": "semresp", "respostasChatbot": [{"colunaMapeada": "R1", "texto": "   "}]},
            "ok": {
                "candidatoId": "ok",
                "respostasChatbot": [{"colunaMapeada": "R1", "texto": "Consigo trabalhar em horário comercial."}],
            },
        },
        decisoes_por_id={
            "ineleg": {"resultado": "inelegivel"},
            "semresp": {"resultado": "elegivel"},
            "ok": {"resultado": "elegivel"},
        },
        template="id {{candidato_id}}\n{{job_description}}\n{{perguntas_respostas}}",
        prompt_id="prm_01",
        mapeamento={"respostasChatbot": ["R1"]},
        job_description_snapshot="Descricao geral da vaga de atendimento.",
        job_description_versao_id="jd_01",
        job_description_vigente_id="jd_01",
    )
    base.update(extra)
    return base


def test_chave_vazia_recusa_lote_sem_cliente(monkeypatch):
    espião = ClienteEspiao()
    monkeypatch.setattr("avaliacao_ia.servico.config.llm_configurada", lambda: False)
    with pytest.raises(RecusaLote) as exc:
        avaliar_lote(ids_selecionados=["ok"], obter_cliente=lambda: espião, **_kwargs())
    assert MSG_CONFIG_AUSENTE in str(exc.value)
    assert espião.chamadas == 0


def test_inelegivel_nao_alcanca_cliente(monkeypatch):
    espião = ClienteEspiao()
    monkeypatch.setattr("avaliacao_ia.servico.config.llm_configurada", lambda: True)
    with pytest.raises(RecusaLote):
        avaliar_lote(ids_selecionados=["ineleg"], obter_cliente=lambda: espião, **_kwargs())
    assert espião.chamadas == 0


def test_elegivel_sem_resposta_nao_alcanca_cliente(monkeypatch):
    espião = ClienteEspiao()
    monkeypatch.setattr("avaliacao_ia.servico.config.llm_configurada", lambda: True)
    with pytest.raises(RecusaLote):
        avaliar_lote(ids_selecionados=["semresp"], obter_cliente=lambda: espião, **_kwargs())
    assert espião.chamadas == 0


def test_cliente_so_para_elegivel_com_resposta(monkeypatch):
    class Ok:
        def __init__(self) -> None:
            self.chamadas = 0
            self.ids: list[str] = []

        def completar(self, mensagens):
            self.chamadas += 1
            user = mensagens[1]["content"]
            assert "ineleg" not in user
            assert "Cabeçalho: R1" in user
            assert "{{criterios_qualitativos}}" not in user
            assert "Disponibilidade de horário" not in user
            trecho = "Consigo trabalhar em horário comercial."
            corpo = {
                "perfil": "A pessoa declara horário comercial nas respostas.",
                "por_pergunta": [
                    {
                        "perguntaId": "p1",
                        "pergunta": "R1",
                        "resultado": "atende",
                        "justificativa": "A resposta declara o horário comercial.",
                    }
                ],
                "trechos": [{"perguntaId": "p1", "trecho": trecho}],
                "nota_tecnica": 80,
                "nota_comportamental": 60,
                "justificativa_nota_tecnica": "A resposta cobre o pedido da vaga. Isso cabe na faixa da rubrica técnica.",
                "justificativa_nota_comportamental": "O texto é claro e organizado. Isso cabe na faixa da escrita.",
            }
            import json

            return {"conteudo": json.dumps(corpo), "uso": {"entrada": 10, "saida": 5, "total": 15, "nota": None}, "tentativasRede": 1}

    cli = Ok()
    monkeypatch.setattr("avaliacao_ia.servico.config.llm_configurada", lambda: True)
    saida = avaliar_lote(
        ids_selecionados=["ineleg", "semresp", "ok"],
        obter_cliente=lambda: cli,
        **_kwargs(),
    )
    assert saida["enviados"] == ["ok"]
    assert cli.chamadas == 1
    assert saida["resultados"][0]["estado"] == "sucesso"
    assert saida["resultados"][0]["compatibilidade"] is None
    assert saida["resultados"][0]["porPergunta"][0]["pergunta"] == "R1"
    assert saida["resultados"][0]["notaTecnica"] == 80
    assert saida["resultados"][0]["notaComportamental"] == 60


def test_compatibilidade_parcial_nao_e_compativel():
    por = [
        {"criterioId": "cq_01", "resultado": "atende"},
        {"criterioId": "cq_02", "resultado": "atende_parcialmente"},
        {"criterioId": "cq_03", "resultado": "atende"},
    ]
    assert calcular_compatibilidade(por, ITENS) == "parcial"


def test_cerca_markdown_nao_impede_json_valido():
    import json

    from avaliacao_ia.prompt import formatar_perguntas_respostas
    from avaliacao_ia.validacao import validar_saida_modelo

    trecho = "Consigo trabalhar em horário comercial."
    respostas = [{"colunaMapeada": "R1", "texto": trecho}]
    bloco = formatar_perguntas_respostas(respostas)
    assert "Pergunta p1" in bloco
    assert "Cabeçalho: R1" in bloco
    corpo = {
        "perfil": "A pessoa declara horário comercial nas respostas.",
        "por_pergunta": [
            {
                "perguntaId": "p1",
                "pergunta": "R1",
                "resultado": "atende",
                "justificativa": "A resposta declara o horário.",
            }
        ],
        "trechos": [{"perguntaId": "p1", "trecho": trecho}],
        "nota_tecnica": 80,
        "nota_comportamental": 60,
        "justificativa_nota_tecnica": "A resposta cobre o pedido da vaga. Isso cabe na faixa da rubrica técnica.",
        "justificativa_nota_comportamental": "O texto é claro e organizado. Isso cabe na faixa da escrita.",
    }
    validado = validar_saida_modelo("```json\n" + json.dumps(corpo) + "\n```", respostas)
    assert validado["perfil"].startswith("A pessoa")
    assert validado["nota_tecnica"] == 80


def test_trecho_fora_da_resposta_falha_e_justificativa_pode_nao_repetir_o_trecho():
    import json

    from avaliacao_ia.validacao import ErroValidacaoJson, validar_saida_modelo

    trecho = "Consigo trabalhar em horário comercial."
    respostas = [{"colunaMapeada": "R1", "texto": trecho}]
    corpo = {
        "perfil": "A pessoa declara horário comercial nas respostas.",
        "por_pergunta": [
            {
                "perguntaId": "p1",
                "pergunta": "R1",
                "resultado": "atende",
                "justificativa": "Há disponibilidade de horário.",
            }
        ],
        "trechos": [{"perguntaId": "p1", "trecho": trecho}],
        "nota_tecnica": 70,
        "nota_comportamental": 60,
        "justificativa_nota_tecnica": "A resposta cobre o pedido da vaga. Isso cabe na faixa da rubrica técnica.",
        "justificativa_nota_comportamental": "O texto é claro e organizado. Isso cabe na faixa da escrita.",
    }
    validado = validar_saida_modelo(json.dumps(corpo), respostas)
    assert validado["por_pergunta"][0]["justificativa"] == "Há disponibilidade de horário."
    assert validado["trechos"][0]["trecho"] == trecho

    corpo["trechos"][0]["trecho"] = "frase que o candidato não escreveu"
    try:
        validar_saida_modelo(json.dumps(corpo), respostas)
        raise AssertionError("trecho inventado deveria falhar")
    except ErroValidacaoJson as erro:
        assert erro.codigo == "trecho_nao_encontrado"


def test_eliminatorio_nao_atende_incompativel():
    por = [
        {"criterioId": "cq_01", "resultado": "atende"},
        {"criterioId": "cq_02", "resultado": "atende"},
        {"criterioId": "cq_03", "resultado": "nao_atende"},
    ]
    assert calcular_compatibilidade(por, ITENS) == "incompativel"
