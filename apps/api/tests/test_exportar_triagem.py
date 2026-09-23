from types import SimpleNamespace

from triagem.exportar import linhas_exportacao


def test_exportacao_na_ordem_da_planilha():
    candidatos = [
        SimpleNamespace(
            candidato_id="2:aa",
            linha_origem=2,
            nome_exibicao="Bia",
            busca_lkd="busca-b",
            email="b@exemplo.com",
            telefone="11999990000",
            ultimo_cargo="Analista de dados sênior",
            idade="30",
            escolaridade="Bacharelado",
        ),
        SimpleNamespace(
            candidato_id="1:bb",
            linha_origem=1,
            nome_exibicao="Leo",
            busca_lkd="busca-a",
            email="",
            telefone="",
            ultimo_cargo="Analista de CRM Sênior",
            idade="33",
            escolaridade="Bacharelado",
        ),
    ]
    decisoes = {
        "1:bb": SimpleNamespace(resultado="elegivel", motivos=[], criterios_inativos=[]),
        "2:aa": SimpleNamespace(
            resultado="inelegivel",
            motivos=[{"mensagem": "Último cargo fora da lista."}],
            criterios_inativos=[],
        ),
    }
    linhas = linhas_exportacao(candidatos, decisoes)
    assert linhas[0][0] == 2
    assert linhas[0][2] == "busca-b"
    assert linhas[0][3] == "b@exemplo.com"
    assert linhas[0][4] == "11999990000"
    assert linhas[0][8] == "Inelegível"
    assert "fora da lista" in linhas[0][9]
    assert linhas[1][1] == "Leo"
    assert linhas[1][8] == "Elegível na triagem"
