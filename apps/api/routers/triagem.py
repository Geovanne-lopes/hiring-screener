from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from persistencia.db import get_db
from persistencia.repositorio import (
    candidato_para_dict,
    criterios_det_vigentes,
    decisoes_por_candidato,
    listar_candidatos,
    obter_projeto,
    substituir_decisoes,
)
from triagem.avaliar import avaliar_candidato, mensagens_bloqueio_execucao
from triagem.exportar import planilha_triagem

router = APIRouter(prefix="/api/projetos", tags=["triagem"])

MSG_SEM_PROJETO = "Abra ou crie um projeto para continuar."


def _exige(db: Session, projeto_id: str):
    projeto = obter_projeto(db, projeto_id)
    if projeto is None:
        raise HTTPException(status_code=400, detail=MSG_SEM_PROJETO)
    return projeto


@router.post("/{projeto_id}/triagem/executar")
def executar(projeto_id: str, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    candidatos = [candidato_para_dict(c) for c in listar_candidatos(db, projeto.id)]
    criterios = criterios_det_vigentes(db, projeto.id)
    bloqueios = mensagens_bloqueio_execucao(criterios, projeto.mapeamento_colunas, len(candidatos))
    if bloqueios:
        raise HTTPException(status_code=400, detail=" ".join(bloqueios))
    assert criterios is not None
    decisoes = []
    for cand in candidatos:
        d = avaliar_candidato(cand, criterios)
        d["criteriosVersao"] = projeto.criterios_det_vigente_id
        decisoes.append(d)
    substituir_decisoes(db, projeto, decisoes, criterios, projeto.criterios_det_vigente_id or "")
    return {"quantidade": len(decisoes), "decisoes": decisoes}


@router.get("/{projeto_id}/triagem")
def get_triagem(projeto_id: str, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    candidatos = listar_candidatos(db, projeto.id)
    decisoes = decisoes_por_candidato(db, projeto.id)
    linhas = []
    for cand in candidatos:
        d = decisoes.get(cand.candidato_id)
        linhas.append(
            {
                **candidato_para_dict(cand),
                "decisao": None
                if d is None
                else {
                    "resultado": d.resultado,
                    "motivos": d.motivos,
                    "criteriosInativos": d.criterios_inativos,
                    "criteriosVersao": d.criterios_versao,
                },
            }
        )
    return {"linhas": linhas}


@router.get("/{projeto_id}/triagem/exportar")
def exportar(projeto_id: str, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    candidatos = listar_candidatos(db, projeto.id)
    decisoes = decisoes_por_candidato(db, projeto.id)
    if not candidatos:
        raise HTTPException(status_code=400, detail="Importe uma planilha antes de exportar a triagem.")
    if not decisoes:
        raise HTTPException(status_code=400, detail="Execute a triagem antes de exportar.")
    conteudo = planilha_triagem(candidatos, decisoes)
    nome = "".join(ch if ch.isalnum() or ch in " -_" else "_" for ch in projeto.nome).strip() or "triagem"
    arquivo = f"triagem-{nome}.xlsx"
    return Response(
        content=conteudo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(arquivo)}"},
    )
