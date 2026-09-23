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
        template="id {{candidato_id}}\n{{criterios_qualitativos}}\n{{respostas_candidato}}",
        prompt_id="prm_01",
        criterios_prompt_versao_id="crt_qual_01",
        criterios_vigente_id="crt_qual_01",
        itens_embutidos=ITENS,
        mapeamento={"respostasChatbot": ["R1"]},
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
            trecho = "Consigo trabalhar em horário comercial."
            corpo = {
                "perfil": "A pessoa declara horário comercial nas respostas.",
                "compatibilidade": "compativel",
                "por_criterio": [
                    {
                        "criterioId": "cq_01",
                        "nome": "Disponibilidade de horário",
                        "resultado": "atende",
                        "justificativa": f'Há declaração: "{trecho}"',
                    },
                    {
                        "criterioId": "cq_02",
                        "nome": "Experiência relatada no atendimento",
                        "resultado": "sem_informacao",
                        "justificativa": "Não há relato de experiência.",
                    },
                    {
                        "criterioId": "cq_03",
                        "nome": "Aderência ao tipo de atendimento",
                        "resultado": "sem_informacao",
                        "justificativa": "Não há informação.",
                    },
                ],
                "trechos": [
                    {"criterioId": "cq_01", "nome": "Disponibilidade de horário", "trecho": trecho},
                    {"criterioId": "cq_02", "nome": "Experiência relatada no atendimento", "trecho": ""},
                    {"criterioId": "cq_03", "nome": "Aderência ao tipo de atendimento", "trecho": ""},
                ],
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
    assert saida["resultados"][0]["compatibilidade"] == "parcial"


def test_compatibilidade_parcial_nao_e_compativel():
    por = [
        {"criterioId": "cq_01", "resultado": "atende"},
        {"criterioId": "cq_02", "resultado": "atende_parcialmente"},
        {"criterioId": "cq_03", "resultado": "atende"},
    ]
    assert calcular_compatibilidade(por, ITENS) == "parcial"


def test_cerca_markdown_nao_impede_json_valido():
    import json

    from avaliacao_ia.prompt import formatar_criterios
    from avaliacao_ia.validacao import validar_saida_modelo

    bloco = formatar_criterios(ITENS)
    assert "criterioId: cq_01" in bloco
    trecho = "Consigo trabalhar em horário comercial."
    corpo = {
        "perfil": "A pessoa declara horário comercial nas respostas.",
        "compatibilidade": "compativel",
        "por_criterio": [
            {
                "criterioId": "cq_01",
                "nome": "Disponibilidade de horário",
                "resultado": "atende",
                "justificativa": trecho,
            },
            {
                "criterioId": "cq_02",
                "nome": "Experiência relatada no atendimento",
                "resultado": "sem_informacao",
                "justificativa": "Não há relato.",
            },
            {
                "criterioId": "cq_03",
                "nome": "Aderência ao tipo de atendimento",
                "resultado": "sem_informacao",
                "justificativa": "Não há informação.",
            },
        ],
        "trechos": [
            {"criterioId": "cq_01", "nome": "Disponibilidade de horário", "trecho": trecho},
            {"criterioId": "cq_02", "nome": "Experiência relatada no atendimento", "trecho": ""},
            {"criterioId": "cq_03", "nome": "Aderência ao tipo de atendimento", "trecho": ""},
        ],
    }
    respostas = [{"colunaMapeada": "R1", "texto": trecho}]
    validado = validar_saida_modelo("```json\n" + json.dumps(corpo) + "\n```", ITENS, respostas)
    assert validado["perfil"].startswith("A pessoa")


def test_justificativa_sem_citacao_recebe_o_trecho():
    import json

    from avaliacao_ia.validacao import ErroValidacaoJson, validar_saida_modelo

    trecho = "Consigo trabalhar em horário comercial."
    corpo = {
        "perfil": "A pessoa declara horário comercial nas respostas.",
        "compatibilidade": "parcial",
        "por_criterio": [
            {
                "criterioId": "cq_01",
                "nome": "Disponibilidade de horário",
                "resultado": "atende",
                "justificativa": "Há disponibilidade de horário.",
            },
            {
                "criterioId": "cq_02",
                "nome": "Experiência relatada no atendimento",
                "resultado": "sem_informacao",
                "justificativa": "Não há relato.",
            },
            {
                "criterioId": "cq_03",
                "nome": "Aderência ao tipo de atendimento",
                "resultado": "sem_informacao",
                "justificativa": "Não há informação.",
            },
        ],
        "trechos": [
            {"criterioId": "cq_01", "nome": "Disponibilidade de horário", "trecho": trecho},
            {"criterioId": "cq_02", "nome": "Experiência relatada no atendimento", "trecho": ""},
            {"criterioId": "cq_03", "nome": "Aderência ao tipo de atendimento", "trecho": ""},
        ],
    }
    respostas = [{"colunaMapeada": "R1", "texto": trecho}]
    validado = validar_saida_modelo(json.dumps(corpo), ITENS, respostas)
    assert trecho in validado["justificativasPorCriterio"][0]["justificativa"]

    corpo["trechos"][0]["trecho"] = "frase que o candidato não escreveu"
    try:
        validar_saida_modelo(json.dumps(corpo), ITENS, respostas)
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
