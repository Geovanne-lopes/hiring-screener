from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from avaliacao_ia.prompt import MSG_JOB_DESCRIPTION_DESALINHADA
from job_description.extrair import MSG_VAZIA, ErroJobDescription, extrair_texto
from persistencia.db import get_db
from persistencia.repositorio import (
    job_description_vigente,
    listar_job_descriptions,
    obter_projeto,
    prompt_vigente,
    salvar_job_description,
)

router = APIRouter(prefix="/api/projetos", tags=["job-description"])

MSG_SEM_PROJETO = "Abra ou crie um projeto para continuar."
MSG_ARQUIVO = "Selecione um arquivo .txt, .md ou .docx."


class JobDescriptionIn(BaseModel):
    texto: str = ""


def _exige(db: Session, projeto_id: str):
    projeto = obter_projeto(db, projeto_id)
    if projeto is None:
        raise HTTPException(status_code=400, detail=MSG_SEM_PROJETO)
    return projeto


def _versao_out(row) -> dict:
    return {
        "jobDescriptionId": row.id,
        "versao": row.versao,
        "projetoId": row.projeto_id,
        "texto": row.texto,
        "criadoEm": row.criado_em.isoformat() if row.criado_em else None,
    }


def _aviso(db: Session, projeto) -> str | None:
    jd = job_description_vigente(db, projeto.id)
    prompt = prompt_vigente(db, projeto)
    if jd is None or prompt is None:
        return None
    if prompt.job_description_versao_id != jd.id:
        return MSG_JOB_DESCRIPTION_DESALINHADA
    return None


@router.get("/{projeto_id}/job-description")
def get_job_description(projeto_id: str, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    vigente = job_description_vigente(db, projeto.id)
    versoes = [_versao_out(row) for row in listar_job_descriptions(db, projeto.id)]
    return {
        "vigente": None if vigente is None else _versao_out(vigente),
        "versoes": versoes,
        "aviso": _aviso(db, projeto),
    }


@router.put("/{projeto_id}/job-description")
def put_job_description(projeto_id: str, body: JobDescriptionIn, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    texto = body.texto.strip()
    if not texto:
        raise HTTPException(status_code=400, detail=MSG_VAZIA)
    row = salvar_job_description(db, projeto, texto)
    return {**_versao_out(row), "aviso": _aviso(db, projeto)}


@router.post("/{projeto_id}/job-description/arquivo")
async def post_arquivo(
    projeto_id: str,
    arquivo: UploadFile | None = File(default=None),
    encoding: str = Form(default="utf-8"),
    db: Session = Depends(get_db),
):
    _exige(db, projeto_id)
    if arquivo is None or not arquivo.filename:
        raise HTTPException(status_code=400, detail=MSG_ARQUIVO)
    conteudo = await arquivo.read()
    try:
        texto = extrair_texto(arquivo.filename, conteudo, encoding)
    except ErroJobDescription as exc:
        raise HTTPException(status_code=400, detail=exc.mensagem) from exc
    return {"texto": texto}
