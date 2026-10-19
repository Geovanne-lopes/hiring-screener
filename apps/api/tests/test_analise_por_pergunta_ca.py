"""CA-P-01 a CA-P-07 da análise por pergunta."""

from __future__ import annotations

import json

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from avaliacao_ia.prompt import MSG_CRITERIOS_FORA, MSG_DELIMITADORES, TEMPLATE_INICIAL
from avaliacao_ia.validacao import ROTULO_SEM_INFORMACAO
from importacao.leitor import MSG_COLUNA_RESPOSTA_SEM_NOME

PERGUNTA_1 = (
    "Como você identifica as necessidades do cliente e personaliza sua abordagem para o atendimento?"
)
PERGUNTA_2 = "Quais ferramentas você usa no atendimento?"
PERGUNTA_3 = "Como você escreve a mensagem ao cliente?"
RESPOSTA_1 = "eu pergunto o que a pessoa já tentou e explico de outro jeito"
RESPOSTA_2 = "uso planilha e um roteiro curto"
RESPOSTA_3 = "escrevo em frases curtas e diretas"
JD = "A vaga pede atendimento consultivo, escuta do cliente e clareza na escrita."
NOME = "Fulana de Tal"
CARGO = "Analista de dados"
TELEFONE = "81999990000"


@pytest.fixture(autouse=True)
def sem_chamada_externa(monkeypatch):
    class ClienteHttpBloqueado(httpx.Client):
        def post(self, *args, **kwargs):
            raise AssertionError("chamada externa")

    monkeypatch.setattr("avaliacao_ia.cliente.httpx.Client", ClienteHttpBloqueado)

    def completar_proibido(self, mensagens):
        raise AssertionError("chamada externa")

    monkeypatch.setattr("avaliacao_ia.cliente.ClienteOpenAICompat.completar", completar_proibido)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SCREENER_DB_PATH", str(tmp_path / "screener.sqlite"))
    import persistencia.db as banco

    banco._engine = None
    banco.init_db()
    from main import app

    with TestClient(app) as c:
        yield c


def _criar(client: TestClient) -> str:
    r = client.post("/api/projetos", json={"nome": "Vaga"})
    assert r.status_code == 200, r.text
    return r.json()["projetoId"]


def _csv(meio: str) -> str:
    return (
        "Nome,Cargo,Idade,Escolaridade,Cidade,Status,Telefone,"
        f'"{PERGUNTA_1}",{PERGUNTA_2},{PERGUNTA_3}\n'
        f"{NOME},{CARGO},34,Bacharelado,Recife,status-legado-xls,{TELEFONE},"
        f"{RESPOSTA_1},{RESPOSTA_2},{RESPOSTA_3}\n"
        f"Beltrana Costa,{CARGO},29,Bacharelado,Recife,status-legado-xls,81988887777,"
        f"{RESPOSTA_1},{meio},{RESPOSTA_3}\n"
        f"Ciclano Souza,Operador de caixa,41,Ensino medio,Olinda,status-legado-xls,81977776666,"
        f"{RESPOSTA_1},{RESPOSTA_2},{RESPOSTA_3}\n"
    )


def _mapa() -> dict:
    return {
        "ultimoCargo": "Cargo",
        "idade": "Idade",
        "escolaridade": "Escolaridade",
        "nomeExibicao": "Nome",
        "respostasChatbot": [PERGUNTA_1, PERGUNTA_2, PERGUNTA_3],
        "cidade": "Cidade",
        "statusLegado": "Status",
    }


def _preparar(client: TestClient, meio: str = RESPOSTA_2) -> tuple[str, dict, dict, dict]:
    pid = _criar(client)
    r = client.put(
        f"/api/projetos/{pid}/criterios-deterministicos",
        json={
            "cargos": {"ativo": True, "aceitos": [CARGO]},
            "idade": {"ativo": False, "minima": None, "maxima": None},
            "escolaridade": {"ativo": False, "configuracao": {"modelo": "lista_valores_aceitos", "aceitos": []}},
        },
    )
    assert r.status_code == 200, r.text
    r = client.post(
        f"/api/projetos/{pid}/importacao/confirmar",
        files={"arquivo": ("lote.csv", _csv(meio).encode("utf-8"), "text/csv")},
        data={"encoding": "utf-8", "mapeamento_json": json.dumps(_mapa())},
    )
    assert r.status_code == 200, r.text
    assert client.post(f"/api/projetos/{pid}/triagem/executar").status_code == 200
    assert client.put(f"/api/projetos/{pid}/job-description", json={"texto": JD}).status_code == 200
    prompt = client.get(f"/api/projetos/{pid}/prompt").json()
    salvo = client.put(f"/api/projetos/{pid}/prompt", json={"template": prompt["templateInicial"]})
    assert salvo.status_code == 200, salvo.text
    linhas = client.get(f"/api/projetos/{pid}/triagem").json()["linhas"]
    por_nome = {l["nomeExibicao"]: l for l in linhas}
    return pid, por_nome[NOME], por_nome["Beltrana Costa"], por_nome["Ciclano Souza"]


def _json_tres(resultados: list[str] | None = None, trechos: list[str] | None = None) -> str:
    perguntas = [PERGUNTA_1, PERGUNTA_2, PERGUNTA_3]
    textos = trechos or [RESPOSTA_1, RESPOSTA_2, RESPOSTA_3]
    julgamentos = resultados or ["atende", "atende", "atende"]
    return json.dumps(
        {
            "perfil": "As respostas descrevem escuta, ferramenta e escrita curta.",
            "por_pergunta": [
                {
                    "perguntaId": f"p{i}",
                    "pergunta": perguntas[i - 1],
                    "resultado": julgamentos[i - 1],
                    "justificativa": "A resposta conversa com a pergunta e com a job description.",
                }
                for i in range(1, 4)
            ],
            "trechos": [
                {"perguntaId": f"p{i}", "trecho": "" if julgamentos[i - 1] == "sem_informacao" else textos[i - 1]}
                for i in range(1, 4)
            ],
            "nota_tecnica": 78,
            "nota_comportamental": 70,
            "justificativa_nota_tecnica": "A resposta cobre o pedido da vaga. Isso cabe na faixa da rubrica técnica.",
            "justificativa_nota_comportamental": "O texto é claro e organizado. Isso cabe na faixa da escrita.",
        }
    )


def _ligar(monkeypatch, conteudo: str):
    class Espiao:
        def __init__(self) -> None:
            self.chamadas = 0
            self.mensagens: list[list[dict]] = []

        def completar(self, mensagens):
            self.chamadas += 1
            self.mensagens.append(mensagens)
            return {
                "conteudo": conteudo,
                "uso": {"entrada": 4, "saida": 3, "total": 7, "nota": None},
                "tentativasRede": 1,
            }

    espiao = Espiao()
    monkeypatch.setattr("avaliacao_ia.servico.config.llm_configurada", lambda: True)
    monkeypatch.setattr("avaliacao_ia.servico.cliente_padrao", lambda: espiao)
    return espiao


def _payload(espiao) -> str:
    return "\n".join(m["content"] for m in espiao.mensagens[0])


def test_ca_p_01_tres_colunas_sem_criterios_qualitativos(client: TestClient, monkeypatch):
    pid, eleg, _parcial, ineleg = _preparar(client)
    espiao = _ligar(monkeypatch, _json_tres())
    disparo = client.post(
        f"/api/projetos/{pid}/avaliacao-ia/executar",
        json={"candidatoIds": [eleg["candidatoId"], ineleg["candidatoId"]], "confirmar": True},
    )
    assert disparo.status_code == 200, disparo.text
    assert disparo.json()["enviados"] == [eleg["candidatoId"]]
    assert espiao.chamadas == 1
    texto = _payload(espiao)
    for pergunta, resposta in (
        (PERGUNTA_1, RESPOSTA_1),
        (PERGUNTA_2, RESPOSTA_2),
        (PERGUNTA_3, RESPOSTA_3),
    ):
        assert f"Cabeçalho: {pergunta}" in texto
        assert resposta in texto
    assert "Pergunta p1" in texto
    assert "Pergunta p2" in texto
    assert "Pergunta p3" in texto
    assert JD in texto
    assert eleg["candidatoId"] in texto
    assert "{{criterios_qualitativos}}" not in texto
    assert "eliminatório" not in texto
    assert "criterioId" not in texto
    limpo = texto.replace(eleg["candidatoId"], "")
    for dado in (NOME, CARGO, "34", "Bacharelado", "Recife", "status-legado-xls", TELEFONE, "Operador de caixa"):
        assert dado not in limpo
    avaliacao = next(
        l["avaliacao"]
        for l in client.get(f"/api/projetos/{pid}/resultado").json()["linhas"]
        if l["candidatoId"] == eleg["candidatoId"]
    )
    assert avaliacao["estado"] == "sucesso"
    assert avaliacao["notaTecnica"] == 78
    assert avaliacao["notaComportamental"] == 70
    assert avaliacao["compatibilidade"] is None
    assert "notaFinal" not in avaliacao
    assert "posicao" not in avaliacao
    assert [p["pergunta"] for p in avaliacao["porPergunta"]] == [PERGUNTA_1, PERGUNTA_2, PERGUNTA_3]


def test_ca_p_02_cabecalho_e_a_pergunta(client: TestClient, monkeypatch):
    pid, eleg, _parcial, _ineleg = _preparar(client)
    espiao = _ligar(monkeypatch, _json_tres())
    disparo = client.post(
        f"/api/projetos/{pid}/avaliacao-ia/executar",
        json={"candidatoIds": [eleg["candidatoId"]], "confirmar": True},
    )
    assert disparo.status_code == 200, disparo.text
    texto = _payload(espiao)
    assert (
        "Pergunta p1\n"
        f"Cabeçalho: {PERGUNTA_1}\n"
        "Resposta:\n"
        f"{RESPOSTA_1}"
    ) in texto
    assert CARGO not in texto
    celula = next(
        item["texto"] for item in eleg["respostasChatbot"] if item["colunaMapeada"] == PERGUNTA_1
    )
    assert celula == RESPOSTA_1


def test_ca_p_03_celula_vazia_nao_viaja(client: TestClient, monkeypatch):
    pid, _eleg, parcial, _ineleg = _preparar(client, meio="   ")
    espiao = _ligar(
        monkeypatch,
        json.dumps(
            {
                "perfil": "Duas respostas sustentam escuta e escrita.",
                "por_pergunta": [
                    {
                        "perguntaId": "p1",
                        "pergunta": PERGUNTA_1,
                        "resultado": "atende",
                        "justificativa": "A resposta descreve a escuta.",
                    },
                    {
                        "perguntaId": "p3",
                        "pergunta": PERGUNTA_3,
                        "resultado": "atende",
                        "justificativa": "A resposta descreve a escrita.",
                    },
                ],
                "trechos": [
                    {"perguntaId": "p1", "trecho": RESPOSTA_1},
                    {"perguntaId": "p3", "trecho": RESPOSTA_3},
                ],
                "nota_tecnica": 60,
                "nota_comportamental": 55,
                "justificativa_nota_tecnica": "A resposta cobre o pedido da vaga. Isso cabe na faixa da rubrica técnica.",
                "justificativa_nota_comportamental": "O texto é claro e organizado. Isso cabe na faixa da escrita.",
            }
        ),
    )
    disparo = client.post(
        f"/api/projetos/{pid}/avaliacao-ia/executar",
        json={"candidatoIds": [parcial["candidatoId"]], "confirmar": True},
    )
    assert disparo.status_code == 200, disparo.text
    texto = _payload(espiao)
    assert f"Cabeçalho: {PERGUNTA_1}" in texto
    assert f"Cabeçalho: {PERGUNTA_3}" in texto
    assert f"Cabeçalho: {PERGUNTA_2}" not in texto
    assert "Pergunta p2" not in texto
    assert RESPOSTA_1 in texto
    assert RESPOSTA_3 in texto
    assert RESPOSTA_2 not in texto


def test_ca_p_04_inelegivel_nao_gera_chamada(client: TestClient, monkeypatch):
    pid, _eleg, _parcial, ineleg = _preparar(client)
    espiao = _ligar(monkeypatch, _json_tres())
    disparo = client.post(
        f"/api/projetos/{pid}/avaliacao-ia/executar",
        json={"candidatoIds": [ineleg["candidatoId"]], "confirmar": True},
    )
    assert disparo.status_code == 400
    assert espiao.chamadas == 0
    assert ineleg["decisao"]["resultado"] == "inelegivel"


def test_ca_p_05_template_com_criterios_qualitativos_nao_salva(client: TestClient):
    pid = _criar(client)
    assert client.put(f"/api/projetos/{pid}/job-description", json={"texto": JD}).status_code == 200
    antes = client.get(f"/api/projetos/{pid}/prompt").json()["versoes"]
    recusa = client.put(
        f"/api/projetos/{pid}/prompt",
        json={"template": "Julgue {{criterios_qualitativos}} com {{job_description}} e {{candidato_id}}."},
    )
    assert recusa.status_code == 400
    assert recusa.json()["detail"] == MSG_CRITERIOS_FORA
    assert client.get(f"/api/projetos/{pid}/prompt").json()["versoes"] == antes

    sem_pergunta = client.put(
        f"/api/projetos/{pid}/prompt",
        json={"template": "{{job_description}}\n{{candidato_id}}"},
    )
    assert sem_pergunta.status_code == 400
    assert sem_pergunta.json()["detail"] == MSG_DELIMITADORES
    assert "INSTRUÇÕES TÉCNICAS" not in TEMPLATE_INICIAL
    assert "{{perguntas_respostas}}" in TEMPLATE_INICIAL


def test_ca_p_06_trecho_fora_da_resposta_nao_grava_nota(client: TestClient, monkeypatch):
    pid, eleg, _parcial, _ineleg = _preparar(client)
    antes = next(
        l for l in client.get(f"/api/projetos/{pid}/triagem").json()["linhas"] if l["candidatoId"] == eleg["candidatoId"]
    )
    ruim = _json_tres(trechos=["escuta do cliente", RESPOSTA_2, RESPOSTA_3])
    espiao = _ligar(monkeypatch, ruim)
    disparo = client.post(
        f"/api/projetos/{pid}/avaliacao-ia/executar",
        json={"candidatoIds": [eleg["candidatoId"]], "confirmar": True},
    )
    assert disparo.status_code == 200, disparo.text
    assert espiao.chamadas == 2
    corpo = disparo.json()["resultados"][0]
    assert corpo["estado"] == "falha_avaliacao"
    linha = next(
        l for l in client.get(f"/api/projetos/{pid}/resultado").json()["linhas"] if l["candidatoId"] == eleg["candidatoId"]
    )
    assert linha["resultadoExibicao"] == "falha_avaliacao"
    assert linha["avaliacao"]["perfil"] is None
    assert linha["avaliacao"]["notaTecnica"] is None
    assert linha["avaliacao"]["notaComportamental"] is None
    assert linha["avaliacao"]["porPergunta"] is None
    depois = next(
        l for l in client.get(f"/api/projetos/{pid}/triagem").json()["linhas"] if l["candidatoId"] == eleg["candidatoId"]
    )
    assert depois["decisao"] == antes["decisao"]


def test_ca_p_07_sem_informacao_nao_vira_atendimento(client: TestClient, monkeypatch):
    pid, eleg, _parcial, _ineleg = _preparar(client)
    espiao = _ligar(monkeypatch, _json_tres(resultados=["sem_informacao", "atende", "atende"]))
    disparo = client.post(
        f"/api/projetos/{pid}/avaliacao-ia/executar",
        json={"candidatoIds": [eleg["candidatoId"]], "confirmar": True},
    )
    assert disparo.status_code == 200, disparo.text
    assert espiao.chamadas == 1
    linha = next(
        l for l in client.get(f"/api/projetos/{pid}/resultado").json()["linhas"] if l["candidatoId"] == eleg["candidatoId"]
    )
    primeira = linha["avaliacao"]["porPergunta"][0]
    assert primeira["resultado"] == "sem_informacao"
    assert primeira["trecho"] == ""
    assert primeira["rotulo"] == ROTULO_SEM_INFORMACAO
    assert primeira["rotulo"] != "atende"
    assert "atendida" not in primeira["rotulo"]
    assert linha["avaliacao"]["compatibilidade"] is None
    bruto = json.dumps(linha["avaliacao"], ensure_ascii=False)
    assert "compativel" not in bruto
    assert "incompativel" not in bruto


def test_cabecalho_vazio_nao_confirma_coluna_de_resposta(client: TestClient):
    pid = _criar(client)
    csv = ",Cargo\nolá,Analista de dados\n"
    mapa = {
        "ultimoCargo": "Cargo",
        "idade": None,
        "escolaridade": None,
        "nomeExibicao": None,
        "respostasChatbot": [""],
        "cidade": None,
        "statusLegado": None,
    }
    r = client.post(
        f"/api/projetos/{pid}/importacao/confirmar",
        files={"arquivo": ("lote.csv", csv.encode("utf-8"), "text/csv")},
        data={"encoding": "utf-8", "mapeamento_json": json.dumps(mapa)},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == MSG_COLUNA_RESPOSTA_SEM_NOME

    unnamed = dict(mapa)
    unnamed["respostasChatbot"] = ["Unnamed: 0"]
    de_novo = client.post(
        f"/api/projetos/{pid}/importacao/confirmar",
        files={"arquivo": ("lote.csv", csv.encode("utf-8"), "text/csv")},
        data={"encoding": "utf-8", "mapeamento_json": json.dumps(unnamed)},
    )
    assert de_novo.status_code == 400
    assert de_novo.json()["detail"] == MSG_COLUNA_RESPOSTA_SEM_NOME


def test_criterios_qualitativos_antigos_nao_entram_no_disparo(client: TestClient, monkeypatch):
    pid, eleg, _parcial, _ineleg = _preparar(client)
    salvo = client.put(
        f"/api/projetos/{pid}/criterios-qualitativos",
        json={
            "itens": [
                {
                    "nome": "Turnos de trabalho",
                    "descricao": "Horarios informados na resposta",
                    "ordem": 1,
                    "eliminatorio": False,
                }
            ]
        },
    )
    assert salvo.status_code == 200, salvo.text
    espiao = _ligar(monkeypatch, _json_tres())
    disparo = client.post(
        f"/api/projetos/{pid}/avaliacao-ia/executar",
        json={"candidatoIds": [eleg["candidatoId"]], "confirmar": True},
    )
    assert disparo.status_code == 200, disparo.text
    assert "Turnos de trabalho" not in _payload(espiao)


def test_template_vigente_antigo_expoe_modelo_sem_salvar(client: TestClient):
    from persistencia.db import SessionLocal
    from persistencia.models import JobDescriptionVersao, Projeto, PromptDoProjeto

    pid = _criar(client)
    jd = client.put(f"/api/projetos/{pid}/job-description", json={"texto": JD})
    assert jd.status_code == 200, jd.text
    db = SessionLocal()
    try:
        projeto = db.get(Projeto, pid)
        assert projeto is not None
        job = db.get(JobDescriptionVersao, jd.json()["jobDescriptionId"])
        assert job is not None
        row = PromptDoProjeto(
            prompt_id=f"prm_{pid}_01",
            versao=1,
            projeto_id=pid,
            template="Antigo {{criterios_qualitativos}} {{job_description}} {{candidato_id}} {{respostas_candidato}}",
            criterios_qualitativos_versao_id="crt_antigo",
            criterios_embutidos_snapshot=[],
            job_description_versao_id=job.id,
            job_description_snapshot=job.texto,
        )
        db.add(row)
        projeto.prompt_vigente_id = row.prompt_id
        db.commit()
    finally:
        db.close()
    corpo = client.get(f"/api/projetos/{pid}/prompt").json()
    assert corpo["templateAntigo"] is True
    assert "{{criterios_qualitativos}}" in corpo["vigente"]["template"]
    assert corpo["modeloRevisao"] == TEMPLATE_INICIAL
    assert "INSTRUÇÕES TÉCNICAS" not in corpo["modeloRevisao"]
    assert client.get(f"/api/projetos/{pid}/prompt").json()["versoes"][0]["versao"] == 1


def test_banco_antigo_ganha_colunas_por_pergunta(tmp_path):
    from persistencia.db import _garantir_colunas_por_pergunta

    engine = create_engine(f"sqlite:///{(tmp_path / 'old.sqlite').as_posix()}")
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE TABLE avaliacoes_ia (id INTEGER PRIMARY KEY)")
    _garantir_colunas_por_pergunta(engine)
    _garantir_colunas_por_pergunta(engine)
    with engine.connect() as conn:
        colunas = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(avaliacoes_ia)")}
    assert {"por_pergunta", "trechos", "nota_tecnica", "nota_comportamental"} <= colunas
