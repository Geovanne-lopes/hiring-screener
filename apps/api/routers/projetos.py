from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from persistencia.db import get_db
from persistencia.repositorio import (
    criar_projeto,
    criterios_det_vigentes,
    duplicar_projeto,
    listar_candidatos,
    listar_projetos,
    obter_projeto,
    renomear_projeto,
    salvar_criterios_det,
)
from triagem.avaliar import criterios_iniciais, incluir_item_lista
from triagem.comparacao import formas_que_tambem_entram, texto_comparado

router = APIRouter(prefix="/api/projetos", tags=["projetos"])

MSG_SEM_PROJETO = "Abra ou crie um projeto para continuar."
MSG_IDADE_INVERTIDA = "Não é possível executar a triagem: a idade mínima é maior que a máxima."


class NomeIn(BaseModel):
    nome: str = Field(min_length=1)


class CargosIn(BaseModel):
    ativo: bool
    aceitos: list[str] = []
    bloqueados: list[str] = []


class EmpresasIn(BaseModel):
    ativo: bool = False
    bloqueadas: list[str] = []


class IdadeIn(BaseModel):
    ativo: bool
    minima: int | None = None
    maxima: int | None = None


class EscolaridadeConfigIn(BaseModel):
    modelo: str = "lista_valores_aceitos"
    aceitos: list[str] = []


class EscolaridadeIn(BaseModel):
    ativo: bool
    configuracao: EscolaridadeConfigIn


class CriteriosDetIn(BaseModel):
    cargos: CargosIn
    idade: IdadeIn
    escolaridade: EscolaridadeIn
    empresas: EmpresasIn = Field(default_factory=EmpresasIn)


def _exige(db: Session, projeto_id: str):
    projeto = obter_projeto(db, projeto_id)
    if projeto is None:
        raise HTTPException(status_code=400, detail=MSG_SEM_PROJETO)
    return projeto


def _projeto_out(db: Session, projeto) -> dict:
    return {
        "projetoId": projeto.id,
        "nome": projeto.nome,
        "criadoEm": projeto.criado_em.isoformat() if projeto.criado_em else None,
        "atualizadoEm": projeto.atualizado_em.isoformat() if projeto.atualizado_em else None,
        "promptVigenteId": projeto.prompt_vigente_id,
        "criteriosDeterministicos": criterios_det_vigentes(db, projeto.id) or criterios_iniciais(),
        "criteriosVersao": projeto.criterios_det_vigente_id,
        "criteriosQualitativosVersaoId": projeto.criterios_qual_vigente_id,
        "jobDescriptionVigenteId": projeto.job_description_vigente_id,
        "mapeamentoColunas": projeto.mapeamento_colunas,
        "quantidadeCandidatos": len(listar_candidatos(db, projeto.id)),
    }


@router.get("")
def get_projetos(db: Session = Depends(get_db)):
    return [_projeto_out(db, p) for p in listar_projetos(db)]


@router.post("")
def post_projeto(body: NomeIn, db: Session = Depends(get_db)):
    nome = body.nome.strip()
    if not nome:
        raise HTTPException(status_code=400, detail="Informe o nome do projeto.")
    return _projeto_out(db, criar_projeto(db, nome))


@router.get("/{projeto_id}")
def get_projeto(projeto_id: str, db: Session = Depends(get_db)):
    return _projeto_out(db, _exige(db, projeto_id))


@router.patch("/{projeto_id}")
def patch_projeto(projeto_id: str, body: NomeIn, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    nome = body.nome.strip()
    if not nome:
        raise HTTPException(status_code=400, detail="Informe o nome do projeto.")
    return _projeto_out(db, renomear_projeto(db, projeto, nome))


@router.post("/{projeto_id}/duplicar")
def post_duplicar(projeto_id: str, body: NomeIn, db: Session = Depends(get_db)):
    origem = _exige(db, projeto_id)
    nome = body.nome.strip()
    if not nome:
        raise HTTPException(status_code=400, detail="Informe o nome do projeto.")
    return _projeto_out(db, duplicar_projeto(db, origem, nome))


def _sanitizar_lista(itens: list[str]) -> tuple[list[str], list[str]]:
    saida: list[str] = []
    avisos: list[str] = []
    for item in itens:
        nova, aviso = incluir_item_lista(saida, item)
        saida = nova
        if aviso:
            avisos.append(aviso)
    return saida, avisos


@router.put("/{projeto_id}/criterios-deterministicos")
def put_criterios(projeto_id: str, body: CriteriosDetIn, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    cargos, avisos_c = _sanitizar_lista(body.cargos.aceitos)
    bloqueados, avisos_b = _sanitizar_lista(body.cargos.bloqueados)
    empresas, avisos_emp = _sanitizar_lista(body.empresas.bloqueadas)
    esc, avisos_e = _sanitizar_lista(body.escolaridade.configuracao.aceitos)
    if body.idade.minima is not None and body.idade.maxima is not None:
        if body.idade.minima > body.idade.maxima:
            raise HTTPException(status_code=400, detail=MSG_IDADE_INVERTIDA)
    snapshot = {
        "cargos": {"ativo": body.cargos.ativo, "aceitos": cargos, "bloqueados": bloqueados},
        "empresas": {"ativo": body.empresas.ativo, "bloqueadas": empresas},
        "idade": {
            "ativo": body.idade.ativo,
            "minima": body.idade.minima,
            "maxima": body.idade.maxima,
        },
        "escolaridade": {
            "ativo": body.escolaridade.ativo,
            "configuracao": {"modelo": "lista_valores_aceitos", "aceitos": esc},
        },
    }
    versao = salvar_criterios_det(db, projeto, snapshot)
    avisos = avisos_c + avisos_b + avisos_emp + avisos_e
    incompletos: list[str] = []
    if snapshot["cargos"]["ativo"] and not snapshot["cargos"]["aceitos"] and not snapshot["cargos"]["bloqueados"]:
        incompletos.append("cargos aceitos e bloqueados")
    if snapshot["idade"]["ativo"] and (
        snapshot["idade"]["minima"] is None or snapshot["idade"]["maxima"] is None
    ):
        incompletos.append("faixa de idade")
    if snapshot["empresas"]["ativo"] and not snapshot["empresas"]["bloqueadas"]:
        incompletos.append("empresas bloqueadas")
    if snapshot["escolaridade"]["ativo"] and not snapshot["escolaridade"]["configuracao"]["aceitos"]:
        incompletos.append("escolaridade")
    return {
        "criteriosVersao": versao.id,
        "criteriosDeterministicos": snapshot,
        "avisos": avisos,
        "incompletos": incompletos,
        "formaComparadaCargos": [
            {
                "original": x,
                "comparado": texto_comparado(x),
                "tambemEntra": formas_que_tambem_entram(x),
            }
            for x in [*cargos, *bloqueados]
        ],
        "formaComparadaEscolaridade": [{"original": x, "comparado": texto_comparado(x)} for x in esc],
    }
