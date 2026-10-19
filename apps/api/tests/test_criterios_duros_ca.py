"""CA-CD-01 a CA-CD-08 de specs/revisao/04-criterios-duros-cargo-empresa-idade.md."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from avaliacao_ia.cliente import ErroClienteLLM
from avaliacao_ia.prompt import TEMPLATE_INICIAL
from avaliacao_ia.servico import _avaliar_um
from importacao.leitor import previsualizar, sugerir_empresa
from triagem.avaliar import (
    MSG_CARGOS_VAZIO,
    MSG_EMPRESAS_VAZIO,
    avaliar_candidato,
    completar_criterios,
    mensagens_bloqueio_execucao,
)
from triagem.comparacao import formas_que_tambem_entram, frase_casa, palavras, parse_idade


def _cand(**kwargs) -> dict:
    base = {
        "candidatoId": "1:abc",
        "projetoId": "prj_01",
        "linhaOrigem": 1,
        "ultimoCargo": "Analista de dados",
        "idade": "34",
        "escolaridade": "Bacharelado",
        "empresa": "Outra",
    }
    base.update(kwargs)
    return base


def _crit(
    *,
    cargo=False,
    idade=False,
    esc=False,
    empresa=False,
    aceitos=None,
    bloqueados=None,
    empresas=None,
    min_=30,
    max_=40,
    esc_aceitos=None,
) -> dict:
    return {
        "cargos": {"ativo": cargo, "aceitos": aceitos or [], "bloqueados": bloqueados or []},
        "empresas": {"ativo": empresa, "bloqueadas": empresas or []},
        "idade": {"ativo": idade, "minima": min_, "maxima": max_},
        "escolaridade": {
            "ativo": esc,
            "configuracao": {"modelo": "lista_valores_aceitos", "aceitos": esc_aceitos or []},
        },
    }


def _codigos(decisao: dict, criterio: str | None = None) -> list[str]:
    motivos = decisao["motivos"]
    if criterio is not None:
        motivos = [m for m in motivos if m["criterio"] == criterio]
    return [m["codigo"] for m in motivos]


def test_ca_cd_01_contains_com_e_sem_traco():
    crit = _crit(cargo=True, aceitos=["Assistente comercial"])
    com_traco = avaliar_candidato(_cand(ultimoCargo="Assistente Comercial - Pleno"), crit)
    sem_traco = avaliar_candidato(_cand(ultimoCargo="Assistente Comercial pleno"), crit)
    assert com_traco["resultado"] == "elegivel"
    assert sem_traco["resultado"] == "elegivel"
    assert palavras("Assistente Comercial - Pleno") == ["assistente", "comercial", "pleno"]
    assert palavras("Assistente Comercial pleno") == ["assistente", "comercial", "pleno"]


def test_ca_cd_02_genero_sem_chamada_de_modelo():
    crit = _crit(cargo=True, aceitos=["Executivo de Negócios"])
    feminino = avaliar_candidato(_cand(ultimoCargo="Executiva de Negócios"), crit)
    ingles = avaliar_candidato(_cand(ultimoCargo="Business Executive"), crit)
    assert feminino["resultado"] == "elegivel"
    assert ingles["resultado"] == "inelegivel"
    assert _codigos(ingles, "cargo") == ["cargo_fora_da_lista"]
    assert frase_casa("Gerente comercial", "Gestor", genero=True, abreviacao=True) is False
    raiz = Path(__file__).resolve().parents[1] / "triagem"
    for path in raiz.rglob("*.py"):
        texto = path.read_text(encoding="utf-8")
        assert "httpx" not in texto
        assert "LLM_" not in texto
    assert "Executiva de Negócios" in formas_que_tambem_entram("Executivo de Negócios")


def test_ca_cd_03_bloqueio_ganha_do_aceito():
    crit = _crit(cargo=True, aceitos=["Assistente comercial"], bloqueados=["Pleno"])
    pleno = avaliar_candidato(_cand(ultimoCargo="Assistente Comercial pleno"), crit)
    assert pleno["resultado"] == "inelegivel"
    assert _codigos(pleno, "cargo") == ["cargo_bloqueado"]
    assert pleno["motivos"][0]["esperado"] == "Pleno"
    assert "Assistente Comercial pleno" in pleno["motivos"][0]["mensagem"]
    assert "assistente comercial pleno" in pleno["motivos"][0]["mensagem"]
    for cargo in ("Assistente Comercial plena", "Assistente Comercial Pl", "Assistente Comercial Pl."):
        d = avaliar_candidato(_cand(ultimoCargo=cargo), crit)
        assert d["resultado"] == "inelegivel"
        assert _codigos(d, "cargo") == ["cargo_bloqueado"]
    for cargo in ("Complementar", "Analista Complementar", "exemplo"):
        d = avaliar_candidato(_cand(ultimoCargo=cargo), _crit(cargo=True, bloqueados=["Pl"]))
        assert "cargo_bloqueado" not in _codigos(d)
    formas = formas_que_tambem_entram("Pleno")
    assert "Plena" in formas
    assert "Pl" in formas


def test_ca_cd_04_sr_pl_e_jr():
    senior = _crit(cargo=True, bloqueados=["Sênior"])
    for cargo in ("Analista Senior", "Analista SR", "Analista Sr."):
        d = avaliar_candidato(_cand(ultimoCargo=cargo), senior)
        assert d["resultado"] == "inelegivel"
        assert _codigos(d) == ["cargo_bloqueado"]
        assert d["motivos"][0]["esperado"] == "Sênior"
    junior = avaliar_candidato(_cand(ultimoCargo="Analista Jr"), _crit(cargo=True, bloqueados=["Júnior"]))
    assert junior["resultado"] == "inelegivel"
    assert _codigos(junior) == ["cargo_bloqueado"]
    ingles = avaliar_candidato(
        _cand(ultimoCargo="Business Executive"),
        _crit(cargo=True, aceitos=["Executivo de Negócios"]),
    )
    assert ingles["resultado"] == "inelegivel"
    assert _codigos(ingles) == ["cargo_fora_da_lista"]
    formas = formas_que_tambem_entram("Sênior")
    assert "Senior" in formas
    assert "Sr" in formas
    assert "Sr." in formas
    assert frase_casa("Sênior de contas", "Sr", genero=True, abreviacao=True) is True


def test_ca_cd_05_lista_vazia_nao_aceita_em_silencio():
    msgs = mensagens_bloqueio_execucao(
        _crit(cargo=True),
        {"ultimoCargo": "Cargo"},
        1,
    )
    assert MSG_CARGOS_VAZIO in msgs
    assert "vazias" in MSG_CARGOS_VAZIO
    so_bloqueio = mensagens_bloqueio_execucao(
        _crit(cargo=True, bloqueados=["Sênior"]),
        {"ultimoCargo": "Cargo"},
        1,
    )
    assert MSG_CARGOS_VAZIO not in so_bloqueio
    inativo = mensagens_bloqueio_execucao(_crit(cargo=False, aceitos=[], bloqueados=[]), {}, 1)
    assert inativo == []


def test_ca_cd_06_empresa_e_payload_do_llm():
    crit = _crit(empresa=True, empresas=["Cielo"])
    cielo = avaliar_candidato(_cand(empresa="Cielo S.A."), crit)
    assert cielo["resultado"] == "inelegivel"
    assert _codigos(cielo) == ["empresa_bloqueada"]
    assert cielo["motivos"][0]["esperado"] == "Cielo"
    grupo = avaliar_candidato(_cand(empresa="Grupo / Cielo"), crit)
    assert _codigos(grupo) == ["empresa_bloqueada"]
    outra = avaliar_candidato(_cand(empresa="Outra empresa"), crit)
    assert outra["resultado"] == "elegivel"
    meio = avaliar_candidato(_cand(empresa="Sociocielo"), crit)
    assert "empresa_bloqueada" not in _codigos(meio)
    vazio = avaliar_candidato(_cand(empresa="  "), crit)
    assert _codigos(vazio) == ["dado_obrigatorio_ausente_ou_invalido"]
    assert vazio["motivos"][0]["criterio"] == "empresa"

    class Espiao:
        def __init__(self) -> None:
            self.mensagens: list = []

        def completar(self, mensagens):
            self.mensagens.append(mensagens)
            raise ErroClienteLLM("rede", "parado")

    espiao = Espiao()
    candidato = _cand(
        empresa="Cielo S.A.",
        ultimoCargo="Executivo de Negócios",
        idade="37 anos e 2 meses",
        nomeExibicao="Fulana de Tal",
        respostasChatbot=[{"colunaMapeada": "Pergunta", "texto": "respondo o que foi perguntado"}],
    )
    _avaliar_um(espiao, candidato, TEMPLATE_INICIAL, "prm_01", "Descricao geral da vaga de atendimento.", None)
    assert espiao.mensagens
    payload = "\n".join(m["content"] for m in espiao.mensagens[0])
    for dado in ("Cielo", "Executivo de Negócios", "37 anos e 2 meses", "Fulana de Tal"):
        assert dado not in payload


def test_ca_cd_07_idade_com_unidade():
    crit = _crit(idade=True, min_=30, max_=40)
    for celula in (
        "37",
        "37.0",
        "37,0",
        "37 Anos",
        "37 - Anos",
        "37anos",
        "37 Años",
        "37 años",
        "37 years",
        "37 anos e 2 meses",
        "37 anos + 2 meses",
        "37 anos + 11 meses",
    ):
        assert parse_idade(celula) == 37
        d = avaliar_candidato(_cand(idade=celula), crit)
        assert d["resultado"] == "elegivel", celula
        assert _codigos(d, "idade") == []
    invalida = avaliar_candidato(_cand(idade="entre 30 e 37 anos"), crit)
    assert invalida["resultado"] == "inelegivel"
    assert _codigos(invalida) == ["dado_obrigatorio_ausente_ou_invalido"]
    assert invalida["motivos"][0]["valorComparado"] is None
    for celula in ("", "adulto", "entre 30 e 37", "30 a 40 anos", "37,5", "0", "121", "#NAME?"):
        assert parse_idade(celula) is None


def test_escolaridade_contains_aceita_bacharelado_dentro_da_celula():
    d = avaliar_candidato(
        _cand(escolaridade="Bacharelado em Estatística"),
        _crit(esc=True, esc_aceitos=["Bacharelado"]),
    )
    assert d["resultado"] == "elegivel"
    assert d["motivos"] == []
    incompleto = avaliar_candidato(
        _cand(escolaridade="Superior incompleto"),
        _crit(esc=True, esc_aceitos=["Ensino Superior"]),
    )
    assert incompleto["resultado"] == "inelegivel"
    assert _codigos(incompleto) == ["escolaridade_fora_da_lista"]


def test_criterio_antigo_sem_bloqueados_nem_empresas():
    antigo = {
        "cargos": {"ativo": True, "aceitos": ["Assistente comercial"]},
        "idade": {"ativo": False, "minima": None, "maxima": None},
        "escolaridade": {"ativo": False, "configuracao": {"modelo": "lista_valores_aceitos", "aceitos": []}},
    }
    completo = completar_criterios(antigo)
    assert completo["cargos"]["bloqueados"] == []
    assert completo["empresas"]["ativo"] is False
    d = avaliar_candidato(_cand(ultimoCargo="Assistente Comercial pleno"), antigo)
    assert d["resultado"] == "elegivel"
    assert "empresa" in d["criteriosInativos"]


def test_ordem_dos_motivos_e_bloqueio_ganha_junto_com_os_outros():
    d = avaliar_candidato(
        _cand(
            ultimoCargo="Vendedor Pleno",
            empresa="Cielo S.A.",
            idade="17",
            escolaridade="Ensino médio",
        ),
        _crit(
            cargo=True,
            empresa=True,
            idade=True,
            esc=True,
            aceitos=["Analista"],
            bloqueados=["Pleno"],
            empresas=["Cielo"],
            min_=30,
            max_=40,
            esc_aceitos=["Bacharelado"],
        ),
    )
    assert [m["criterio"] for m in d["motivos"]] == ["cargo", "cargo", "empresa", "idade", "escolaridade"]
    assert [m["codigo"] for m in d["motivos"]] == [
        "cargo_fora_da_lista",
        "cargo_bloqueado",
        "empresa_bloqueada",
        "idade_fora_da_faixa",
        "escolaridade_fora_da_lista",
    ]


def test_empresa_ativa_vazia_ou_sem_coluna_recusa_o_lote():
    vazia = mensagens_bloqueio_execucao(_crit(empresa=True), {"empresa": "Empresa"}, 1)
    assert MSG_EMPRESAS_VAZIO in vazia
    sem_coluna = mensagens_bloqueio_execucao(_crit(empresa=True, empresas=["Cielo"]), {}, 1)
    assert any("empresa" in m and "não foi mapeada" in m for m in sem_coluna)
    inativa = mensagens_bloqueio_execucao(_crit(empresa=False, empresas=["Cielo"]), {}, 1)
    assert inativa == []


def test_sugerir_empresa_so_quando_o_cabecalho_e_empresa():
    assert sugerir_empresa(["Nome", " Empresa ", "Cargo"]) == " Empresa "
    assert sugerir_empresa(["empresa", "Cargo"]) is None
    preview = previsualizar("Nome,Empresa\nAna,Cielo\n".encode("utf-8"), "lote.csv", "utf-8")
    assert preview["sugestaoEmpresa"] == "Empresa"


@pytest.fixture(autouse=True)
def sem_chamada_externa(monkeypatch):
    class ClienteHttpBloqueado(httpx.Client):
        def post(self, *args, **kwargs):
            raise AssertionError("chamada externa")

    monkeypatch.setattr("avaliacao_ia.cliente.httpx.Client", ClienteHttpBloqueado)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SCREENER_DB_PATH", str(tmp_path / "screener.sqlite"))
    import persistencia.db as banco

    banco._engine = None
    banco.init_db()
    from main import app

    with TestClient(app) as c:
        yield c


def test_triagem_pleno_passa_e_sr_cai(client: TestClient):
    projeto = client.post("/api/projetos", json={"nome": "Vaga comercial"})
    assert projeto.status_code == 200, projeto.text
    pid = projeto.json()["projetoId"]
    salvo = client.put(
        f"/api/projetos/{pid}/criterios-deterministicos",
        json={
            "cargos": {"ativo": True, "aceitos": ["Assistente comercial"], "bloqueados": ["Sênior"]},
            "empresas": {"ativo": True, "bloqueadas": ["Cielo"]},
            "idade": {"ativo": True, "minima": 30, "maxima": 40},
            "escolaridade": {"ativo": False, "configuracao": {"modelo": "lista_valores_aceitos", "aceitos": []}},
        },
    )
    assert salvo.status_code == 200, salvo.text
    assert "Plena" in salvo.json()["formaComparadaCargos"][-1]["tambemEntra"] or any(
        "Sr" in item["tambemEntra"] for item in salvo.json()["formaComparadaCargos"]
    )
    csv = (
        "Nome,Cargo,Idade,Empresa,Escolaridade\n"
        "Ana,Assistente Comercial pleno,37 anos e 2 meses,Outra,Bacharelado\n"
        "Bia,Analista SR,34,Cielo S.A.,Bacharelado\n"
    )
    mapa = {
        "ultimoCargo": "Cargo",
        "idade": "Idade",
        "escolaridade": "Escolaridade",
        "empresa": "Empresa",
        "nomeExibicao": "Nome",
        "respostasChatbot": [],
    }
    lote = client.post(
        f"/api/projetos/{pid}/importacao/confirmar",
        files={"arquivo": ("lote.csv", csv.encode("utf-8"), "text/csv")},
        data={"encoding": "utf-8", "mapeamento_json": json.dumps(mapa)},
    )
    assert lote.status_code == 200, lote.text
    triagem = client.post(f"/api/projetos/{pid}/triagem/executar")
    assert triagem.status_code == 200, triagem.text
    por_nome = {linha["nomeExibicao"]: linha for linha in client.get(f"/api/projetos/{pid}/triagem").json()["linhas"]}
    ana = por_nome["Ana"]
    bia = por_nome["Bia"]
    assert ana["decisao"]["resultado"] == "elegivel"
    assert ana["ultimoCargo"] == "Assistente Comercial pleno"
    assert ana["empresa"] == "Outra"
    assert bia["decisao"]["resultado"] == "inelegivel"
    assert [m["codigo"] for m in bia["decisao"]["motivos"]] == [
        "cargo_fora_da_lista",
        "cargo_bloqueado",
        "empresa_bloqueada",
    ]
    bloqueio = next(m for m in bia["decisao"]["motivos"] if m["codigo"] == "cargo_bloqueado")
    assert bloqueio["esperado"] == "Sênior"
    assert bia["empresa"] == "Cielo S.A."

    copia = client.post(f"/api/projetos/{pid}/duplicar", json={"nome": "Copia"})
    assert copia.status_code == 200, copia.text
    criterios = copia.json()["criteriosDeterministicos"]
    assert criterios["empresas"]["bloqueadas"] == ["Cielo"]
    assert criterios["cargos"]["bloqueados"] == ["Sênior"]
    assert copia.json()["quantidadeCandidatos"] == 0


def test_leitura_de_snapshot_antigo_na_api(client: TestClient):
    projeto = client.post("/api/projetos", json={"nome": "Antigo"})
    pid = projeto.json()["projetoId"]
    import persistencia.db as banco
    from persistencia.models import CriteriosDeterministicosVersao
    from persistencia.repositorio import obter_projeto

    db = banco.SessionLocal()
    row_projeto = obter_projeto(db, pid)
    assert row_projeto is not None
    row = db.get(CriteriosDeterministicosVersao, row_projeto.criterios_det_vigente_id)
    assert row is not None
    row.snapshot = {
        "cargos": {"ativo": True, "aceitos": ["Assistente comercial"]},
        "idade": {"ativo": False, "minima": None, "maxima": None},
        "escolaridade": {"ativo": False, "configuracao": {"modelo": "lista_valores_aceitos", "aceitos": []}},
    }
    db.commit()
    db.close()
    lido = client.get(f"/api/projetos/{pid}")
    assert lido.status_code == 200, lido.text
    criterios = lido.json()["criteriosDeterministicos"]
    assert criterios["cargos"]["bloqueados"] == []
    assert criterios["empresas"]["ativo"] is False
    csv = "Nome,Cargo\nAna,Assistente Comercial pleno\n"
    lote = client.post(
        f"/api/projetos/{pid}/importacao/confirmar",
        files={"arquivo": ("lote.csv", csv.encode("utf-8"), "text/csv")},
        data={
            "encoding": "utf-8",
            "mapeamento_json": json.dumps({"ultimoCargo": "Cargo", "nomeExibicao": "Nome", "respostasChatbot": []}),
        },
    )
    assert lote.status_code == 200, lote.text
    triagem = client.post(f"/api/projetos/{pid}/triagem/executar")
    assert triagem.status_code == 200, triagem.text
    linha = triagem.json()["decisoes"][0]
    assert linha["resultado"] == "elegivel"
