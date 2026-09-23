from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook

from persistencia.models import CandidatoImportado, DecisaoTriagem

COLUNAS = [
    "Linha",
    "Nome",
    "Busca LKD",
    "Email",
    "Telefone",
    "Cargo",
    "Idade",
    "Escolaridade",
    "Decisão",
    "Motivos",
    "Critérios não aplicados",
]

_ROTULO = {
    "elegivel": "Elegível na triagem",
    "inelegivel": "Inelegível",
}


def linhas_exportacao(
    candidatos: list[CandidatoImportado],
    decisoes: dict[str, DecisaoTriagem],
) -> list[list]:
    linhas: list[list] = []
    for cand in candidatos:
        decisao = decisoes.get(cand.candidato_id)
        if decisao is None:
            rotulo = ""
            motivos = ""
            inativos = ""
        else:
            rotulo = _ROTULO.get(decisao.resultado, decisao.resultado)
            motivos = " | ".join(
                str(m.get("mensagem") or "") for m in (decisao.motivos or []) if isinstance(m, dict)
            )
            inativos = ", ".join(str(n) for n in (decisao.criterios_inativos or []))
        linhas.append(
            [
                cand.linha_origem,
                cand.nome_exibicao or "",
                cand.busca_lkd or "",
                cand.email or "",
                cand.telefone or "",
                cand.ultimo_cargo or "",
                cand.idade or "",
                cand.escolaridade or "",
                rotulo,
                motivos,
                inativos,
            ]
        )
    return linhas


def planilha_triagem(
    candidatos: list[CandidatoImportado],
    decisoes: dict[str, DecisaoTriagem],
) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Triagem"
    ws.append(COLUNAS)
    for linha in linhas_exportacao(candidatos, decisoes):
        ws.append(linha)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
