"""Excel da avaliação. Não substitui a planilha da triagem determinística."""

from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook

COLUNAS = [
    "Linha",
    "Nome",
    "Email",
    "Telefone",
    "Nota técnica",
    "Justificativa da nota técnica",
    "Ranking técnico",
    "Nota comportamental",
    "Justificativa da nota comportamental",
    "Ranking comportamental",
    "Nota final",
    "Ranking final",
    "Perguntas",
    "Resumo",
]

_ROTULOS = {
    "atende": "atende",
    "atende_parcialmente": "atende parcialmente",
    "nao_atende": "não atende",
    "sem_informacao": "sem informação",
}


def juntar_perguntas(por_pergunta: list | None) -> str:
    if not por_pergunta:
        return ""
    partes: list[str] = []
    for item in por_pergunta:
        if not isinstance(item, dict):
            continue
        cabecalho = item.get("pergunta") or ""
        resultado = item.get("resultado") or ""
        rotulo = _ROTULOS.get(resultado, resultado)
        partes.append(f"{cabecalho}: {rotulo}")
    return " | ".join(partes)


def justificativas_da_linha(por_pergunta: list | None) -> list[str]:
    if not por_pergunta:
        return []
    saida: list[str] = []
    for item in por_pergunta:
        if not isinstance(item, dict):
            continue
        saida.append((item.get("justificativa") or "").strip())
    return saida


def cabecalho_exportacao(quantidade_perguntas: int) -> list[str]:
    return [
        *COLUNAS,
        *[f"Justificativa pergunta {indice}" for indice in range(1, quantidade_perguntas + 1)],
    ]


def tabela_exportacao(linhas: list[dict], contatos: dict[str, dict]) -> tuple[list[str], list[list]]:
    corpos: list[list] = []
    justificativas: list[list[str]] = []
    for linha in linhas:
        contato = contatos.get(linha["candidatoId"]) or {}
        ranking = linha.get("ranking") or {}
        avaliacao = linha.get("avaliacao") or {}
        tem_nota = ranking.get("posicaoFinal") is not None
        if tem_nota:
            notas = [
                avaliacao.get("notaTecnica"),
                (avaliacao.get("justificativaNotaTecnica") or "").strip() or None,
                ranking.get("posicaoTecnica"),
                avaliacao.get("notaComportamental"),
                (avaliacao.get("justificativaNotaComportamental") or "").strip() or None,
                ranking.get("posicaoComportamental"),
                ranking.get("notaFinal"),
                ranking.get("posicaoFinal"),
            ]
        else:
            notas = [None, None, None, None, None, None, None, None]
        corpos.append(
            [
                linha["linhaOrigem"],
                contato.get("nome") or "",
                contato.get("email") or "",
                contato.get("telefone") or "",
                *notas,
                juntar_perguntas(avaliacao.get("porPergunta")),
                (avaliacao.get("perfil") or "").strip(),
            ]
        )
        justificativas.append(justificativas_da_linha(avaliacao.get("porPergunta")))
    quantidade = max((len(itens) for itens in justificativas), default=0)
    saida = [
        [*corpo, *itens, *([None] * (quantidade - len(itens)))]
        for corpo, itens in zip(corpos, justificativas, strict=True)
    ]
    return cabecalho_exportacao(quantidade), saida


def linhas_exportacao(linhas: list[dict], contatos: dict[str, dict]) -> list[list]:
    _, tabela = tabela_exportacao(linhas, contatos)
    return tabela


def planilha_resultado(linhas: list[dict], contatos: dict[str, dict]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Resultado"
    cabecalho, tabela = tabela_exportacao(linhas, contatos)
    ws.append(cabecalho)
    for linha in tabela:
        ws.append(linha)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
