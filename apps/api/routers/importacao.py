from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from importacao.leitor import ErroImportacao, confirmar_lote, previsualizar
from persistencia.db import get_db
from persistencia.repositorio import obter_projeto, substituir_lote

router = APIRouter(prefix="/api/projetos", tags=["importacao"])

MSG_SEM_PROJETO = "Abra ou crie um projeto para continuar."
MSG_ARQUIVO = "Selecione um arquivo CSV ou XLSX para importar."


def _exige(db: Session, projeto_id: str):
    projeto = obter_projeto(db, projeto_id)
    if projeto is None:
        raise HTTPException(status_code=400, detail=MSG_SEM_PROJETO)
    return projeto


@router.post("/{projeto_id}/importacao/preview")
async def preview(
    projeto_id: str,
    arquivo: UploadFile | None = File(default=None),
    encoding: str = Form(default="latin-1"),
    db: Session = Depends(get_db),
):
    _exige(db, projeto_id)
    if arquivo is None or not arquivo.filename:
        raise HTTPException(status_code=400, detail=MSG_ARQUIVO)
    conteudo = await arquivo.read()
    if not conteudo:
        raise HTTPException(status_code=400, detail=MSG_ARQUIVO)
    try:
        return previsualizar(conteudo, arquivo.filename, encoding)
    except ErroImportacao as exc:
        raise HTTPException(status_code=400, detail=exc.mensagem) from exc


@router.post("/{projeto_id}/importacao/confirmar")
async def confirmar(
    projeto_id: str,
    arquivo: UploadFile | None = File(default=None),
    encoding: str = Form(default="latin-1"),
    mapeamento_json: str = Form(default="{}"),
    db: Session = Depends(get_db),
):
    projeto = _exige(db, projeto_id)
    if arquivo is None or not arquivo.filename:
        raise HTTPException(status_code=400, detail=MSG_ARQUIVO)
    conteudo = await arquivo.read()
    if not conteudo:
        raise HTTPException(status_code=400, detail=MSG_ARQUIVO)
    try:
        mapeamento = json.loads(mapeamento_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Mapeamento inválido.") from exc
    try:
        candidatos = confirmar_lote(conteudo, arquivo.filename, encoding, mapeamento, projeto.id)
    except ErroImportacao as exc:
        raise HTTPException(status_code=400, detail=exc.mensagem) from exc
    substituir_lote(db, projeto, mapeamento, candidatos)
    return {
        "quantidade": len(candidatos),
        "mapeamentoColunas": mapeamento,
        "candidatos": [
            {
                "candidatoId": c["candidatoId"],
                "linhaOrigem": c["linhaOrigem"],
                "nomeExibicao": c.get("nomeExibicao"),
                "ultimoCargo": c.get("ultimoCargo"),
            }
            for c in candidatos[:20]
        ],
    }
