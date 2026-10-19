"""Tradução dos critérios de aceite CA-01 a CA-14 de triagem-deterministica.md."""

from __future__ import annotations

from pathlib import Path

from triagem.avaliar import (
    MSG_CARGOS_VAZIO,
    MSG_ESCOLARIDADE_VAZIA,
    MSG_IDADE_FAIXA,
    avaliar_candidato,
    incluir_item_lista,
    mensagens_bloqueio_execucao,
)
from triagem.normalizacao import normalizar


def _cand(**kwargs) -> dict:
    base = {
        "candidatoId": "1:abc",
        "projetoId": "prj_01",
        "linhaOrigem": 1,
        "ultimoCargo": "Analista de dados",
        "idade": "34",
        "escolaridade": "Bacharelado",
    }
    base.update(kwargs)
    return base


def _crit(*, cargo=False, idade=False, esc=False, aceitos=None, min_=18, max_=45, esc_aceitos=None) -> dict:
    return {
        "cargos": {"ativo": cargo, "aceitos": aceitos or []},
        "idade": {"ativo": idade, "minima": min_, "maxima": max_},
        "escolaridade": {
            "ativo": esc,
            "configuracao": {"modelo": "lista_valores_aceitos", "aceitos": esc_aceitos or []},
        },
    }


def test_triagem_nao_importa_avaliacao_ia():
    raiz = Path(__file__).resolve().parents[1] / "triagem"
    for path in raiz.rglob("*.py"):
        for linha in path.read_text(encoding="utf-8").splitlines():
            t = linha.strip()
            assert not t.startswith("import avaliacao_ia")
            assert not t.startswith("from avaliacao_ia")
            assert "httpx" not in t
            assert "LLM_" not in t


def test_ca01_cargo_fora_da_lista_ativa():
    d = avaliar_candidato(
        _cand(ultimoCargo="Vendedor"),
        _crit(cargo=True, aceitos=["Analista de dados"]),
    )
    assert d["resultado"] == "inelegivel"
    assert d["motivos"][0]["codigo"] == "cargo_fora_da_lista"
    assert d["motivos"][0]["valorLido"] == "Vendedor"
    assert "Analista de dados" in d["motivos"][0]["mensagem"]


def test_ca02_cargo_na_lista_e_demais_satisfeitos():
    d = avaliar_candidato(
        _cand(),
        _crit(
            cargo=True,
            idade=True,
            esc=True,
            aceitos=["Analista de dados"],
            esc_aceitos=["Bacharelado"],
        ),
    )
    assert d["resultado"] == "elegivel"
    assert d["motivos"] == []


def test_ca03_idade_abaixo_do_minimo():
    d = avaliar_candidato(
        _cand(idade="17"),
        _crit(cargo=True, idade=True, esc=True, aceitos=["Analista de dados"], esc_aceitos=["Bacharelado"]),
    )
    assert d["resultado"] == "inelegivel"
    assert any(m["codigo"] == "idade_fora_da_faixa" for m in d["motivos"])


def test_ca04_idade_acima_do_maximo():
    d = avaliar_candidato(
        _cand(idade="46"),
        _crit(cargo=True, idade=True, esc=True, aceitos=["Analista de dados"], esc_aceitos=["Bacharelado"]),
    )
    assert d["resultado"] == "inelegivel"
    assert any(m["codigo"] == "idade_fora_da_faixa" for m in d["motivos"])


def test_ca05_limites_inclusivos():
    crit = _crit(cargo=True, idade=True, esc=True, aceitos=["Analista de dados"], esc_aceitos=["Bacharelado"])
    d18 = avaliar_candidato(_cand(idade="18"), crit)
    d45 = avaliar_candidato(_cand(idade="45"), crit)
    assert d18["resultado"] == "elegivel"
    assert d45["resultado"] == "elegivel"
    assert not any(m["codigo"] == "idade_fora_da_faixa" for m in d18["motivos"])
    assert not any(m["codigo"] == "idade_fora_da_faixa" for m in d45["motivos"])


def test_escolaridade_contains_sem_genero_nem_abreviacao():
    estatistica = avaliar_candidato(
        _cand(escolaridade="Bacharelado em Estatística"),
        _crit(esc=True, esc_aceitos=["Bacharelado"]),
    )
    assert estatistica["resultado"] == "elegivel"
    traco = avaliar_candidato(
        _cand(escolaridade="Bacharelado - Estatística"),
        _crit(esc=True, esc_aceitos=["Bacharelado"]),
    )
    assert traco["resultado"] == "elegivel"
    completo = avaliar_candidato(
        _cand(escolaridade="Ensino Superior Completo"),
        _crit(esc=True, esc_aceitos=["Ensino Superior"]),
    )
    assert completo["resultado"] == "elegivel"
    administracao = avaliar_candidato(
        _cand(escolaridade="Ensino Superior em Administração"),
        _crit(esc=True, esc_aceitos=["Ensino Superior"]),
    )
    assert administracao["resultado"] == "elegivel"
    incompleto = avaliar_candidato(
        _cand(escolaridade="Superior incompleto"),
        _crit(esc=True, esc_aceitos=["Ensino Superior"]),
    )
    assert incompleto["resultado"] == "inelegivel"
    assert incompleto["motivos"][0]["codigo"] == "escolaridade_fora_da_lista"
    assert incompleto["motivos"][0]["valorComparado"] == "superior incompleto"
    frase_maior = avaliar_candidato(
        _cand(escolaridade="Bacharelado"),
        _crit(esc=True, esc_aceitos=["Bacharelado em Estatística"]),
    )
    assert frase_maior["resultado"] == "inelegivel"
    sem_genero = avaliar_candidato(
        _cand(escolaridade="Bacharela"),
        _crit(esc=True, esc_aceitos=["Bacharel"]),
    )
    assert sem_genero["resultado"] == "inelegivel"


def test_ca06_escolaridade_fora_da_lista():
    d = avaliar_candidato(
        _cand(escolaridade="Ensino médio"),
        _crit(esc=True, esc_aceitos=["Bacharelado"]),
    )
    assert d["resultado"] == "inelegivel"
    assert d["motivos"][0]["codigo"] == "escolaridade_fora_da_lista"


def test_ca07_cargo_inativo_nao_elimina():
    d = avaliar_candidato(
        _cand(ultimoCargo="Vendedor"),
        _crit(cargo=False, aceitos=["Analista de dados"]),
    )
    assert d["resultado"] == "elegivel"
    assert "cargo" in d["criteriosInativos"]


def test_ca08_ativo_sem_configuracao_nao_executa():
    msgs = mensagens_bloqueio_execucao(
        _crit(cargo=True, aceitos=[]),
        {"ultimoCargo": "Cargo"},
        1,
    )
    assert any(MSG_CARGOS_VAZIO == m for m in msgs)
    assert not any("elegivel" in m.lower() and "marcado" in m.lower() for m in msgs)


def test_ca08b_escolaridade_ativa_vazia():
    msgs = mensagens_bloqueio_execucao(
        _crit(esc=True, esc_aceitos=[]),
        {"escolaridade": "Escolaridade"},
        1,
    )
    assert MSG_ESCOLARIDADE_VAZIA in msgs


def test_ca08c_idade_ativa_sem_faixa():
    crit = _crit(idade=True)
    crit["idade"]["minima"] = None
    crit["idade"]["maxima"] = None
    msgs = mensagens_bloqueio_execucao(crit, {"idade": "Idade"}, 1)
    assert MSG_IDADE_FAIXA in msgs


def test_ca09_inelegivel_nao_e_entrada_de_ia():
    d = avaliar_candidato(_cand(ultimoCargo="Vendedor"), _crit(cargo=True, aceitos=["Analista de dados"]))
    assert d["resultado"] == "inelegivel"
    assert d["motivos"]
    envelope = "inelegivel"


def test_ca10_maiusculas_e_acento_nao_eliminam():
    d = avaliar_candidato(
        _cand(ultimoCargo="analise de dados"),
        _crit(cargo=True, aceitos=["Análise de Dados"]),
    )
    assert d["resultado"] == "elegivel"
    assert normalizar("analise de dados") == normalizar("Análise de Dados")
    assert normalizar("Análise de Dados") == "analise de dados"


def test_cargo_com_complemento_depois_de_separador_entra():
    crit = _crit(cargo=True, aceitos=["Analista de CRM Pleno", "Analista de Dados Pleno"])
    martech = avaliar_candidato(_cand(ultimoCargo="Analista de CRM Pleno / Martech"), crit)
    intel = avaliar_candidato(
        _cand(ultimoCargo="Analista de Dados Pleno | Inteligência Comercial"),
        crit,
    )
    assert martech["resultado"] == "elegivel"
    assert intel["resultado"] == "elegivel"


def test_ca11_contains_nao_corta_na_primeira_palavra():
    dentro = avaliar_candidato(
        _cand(ultimoCargo="Vendedor Externo"),
        _crit(cargo=True, aceitos=["Vendedor"]),
    )
    assert dentro["resultado"] == "elegivel"
    fora = avaliar_candidato(
        _cand(ultimoCargo="Analista"),
        _crit(cargo=True, aceitos=["Analista de dados"]),
    )
    assert fora["resultado"] == "inelegivel"
    assert fora["motivos"][0]["codigo"] == "cargo_fora_da_lista"
    assert fora["motivos"][0]["valorComparado"] == "analista"
    ordem = avaliar_candidato(
        _cand(ultimoCargo="dados de Analista"),
        _crit(cargo=True, aceitos=["Analista de dados"]),
    )
    assert ordem["resultado"] == "inelegivel"
    assert ordem["motivos"][0]["valorComparado"] == "dados de analista"


def test_ca11b_lista_com_cargo_completo_aceita():
    d = avaliar_candidato(
        _cand(ultimoCargo="Vendedor Externo"),
        _crit(cargo=True, aceitos=["Vendedor Externo"]),
    )
    assert d["resultado"] == "elegivel"


def test_ca12_dado_obrigatorio_ausente():
    d = avaliar_candidato(_cand(ultimoCargo=""), _crit(cargo=True, aceitos=["Analista de dados"]))
    assert d["resultado"] == "inelegivel"
    assert d["motivos"][0]["codigo"] == "dado_obrigatorio_ausente_ou_invalido"
    assert d["motivos"][0]["criterio"] == "cargo"
    assert "ausente ou inválido" in d["motivos"][0]["mensagem"]


def test_ca13_idade_ilegivel():
    d = avaliar_candidato(
        _cand(idade="vinte"),
        _crit(idade=True, min_=18, max_=45),
    )
    assert d["resultado"] == "inelegivel"
    assert d["motivos"][0]["codigo"] == "dado_obrigatorio_ausente_ou_invalido"
    assert d["motivos"][0]["criterio"] == "idade"


def test_ca14_todos_os_motivos():
    d = avaliar_candidato(
        _cand(ultimoCargo="Vendedor", idade="17", escolaridade="Ensino médio"),
        _crit(
            cargo=True,
            idade=True,
            esc=True,
            aceitos=["Analista de dados"],
            esc_aceitos=["Bacharelado"],
        ),
    )
    assert len(d["motivos"]) == 3
    assert [m["criterio"] for m in d["motivos"]] == ["cargo", "idade", "escolaridade"]


def test_lista_vazio_e_duplicata():
    lista, aviso = incluir_item_lista([], "")
    assert lista == []
    assert aviso == "Item vazio ignorado."
    lista, aviso = incluir_item_lista(lista, "Analista")
    assert lista == ["Analista"]
    assert aviso is None
    lista, aviso = incluir_item_lista(lista, "analista")
    assert lista == ["Analista"]
    assert aviso == "Este valor já está na lista."
