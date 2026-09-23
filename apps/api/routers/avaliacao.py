from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import config
from avaliacao_ia.prompt import (
    TEMPLATE_INICIAL,
    parece_regra_dura,
    validar_template,
)
from avaliacao_ia.resposta import resposta_utilizavel
from avaliacao_ia.servico import RecusaLote, avaliar_lote, montar_preview, recusar_se_nao_configurado
from persistencia.db import get_db
from persistencia.repositorio import (
    avaliacao_mais_recente,
    candidato_para_dict,
    criterios_qual_vigentes,
    decisoes_por_candidato,
    gravar_avaliacao,
    listar_candidatos,
    listar_prompts,
    novo_id,
    obter_projeto,
    prompt_vigente,
    salvar_criterios_qual,
    salvar_prompt,
)
from texto_util import normalizar

router = APIRouter(prefix="/api/projetos", tags=["avaliacao"])

MSG_SEM_PROJETO = "Abra ou crie um projeto para continuar."
PEDIDO_TRAJETORIA = {
    "acao": "avaliar_trajetoria",
    "habilitada": False,
    "mensagem": "Avaliar trajetória vem em sprint posterior.",
}


class ItemQualIn(BaseModel):
    criterioId: str | None = None
    nome: str
    descricao: str
    ordem: int
    eliminatorio: bool = False


class CriteriosQualIn(BaseModel):
    itens: list[ItemQualIn]
    confirmarRegraDura: bool = False


class PromptIn(BaseModel):
    template: str


class PreviewIn(BaseModel):
    candidatoId: str | None = None


class AvaliarIn(BaseModel):
    candidatoIds: list[str] = Field(default_factory=list)
    confirmar: bool = False


def _exige(db: Session, projeto_id: str):
    projeto = obter_projeto(db, projeto_id)
    if projeto is None:
        raise HTTPException(status_code=400, detail=MSG_SEM_PROJETO)
    return projeto


@router.get("/{projeto_id}/criterios-qualitativos")
def get_qual(projeto_id: str, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    vigente = criterios_qual_vigentes(db, projeto.id)
    return {
        "projetoId": projeto.id,
        "versaoId": None if vigente is None else vigente.id,
        "itens": [] if vigente is None else vigente.itens,
        "avisoRegraDura": (
            "Cargo, idade e escolaridade já foram aplicados na triagem. "
            "Não cadastre esses critérios aqui para o modelo decidir quem entra. "
            "O modelo não reabre a porta de entrada."
        ),
    }


@router.put("/{projeto_id}/criterios-qualitativos")
def put_qual(projeto_id: str, body: CriteriosQualIn, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    avisos: list[str] = []
    nomes_vistos: list[str] = []
    itens_out: list[dict] = []
    ids_existentes = {}
    vigente = criterios_qual_vigentes(db, projeto.id)
    if vigente:
        for item in vigente.itens:
            ids_existentes[item.get("criterioId")] = item
    for bruto in body.itens:
        nome = bruto.nome.strip()
        descricao = bruto.descricao.strip()
        if not nome or not descricao:
            avisos.append("Item vazio ignorado.")
            continue
        if any(normalizar(n) == normalizar(nome) for n in nomes_vistos):
            raise HTTPException(status_code=400, detail="Já existe um critério com este nome.")
        nomes_vistos.append(nome)
        cid = bruto.criterioId if bruto.criterioId and bruto.criterioId in ids_existentes else novo_id("cq")
        itens_out.append(
            {
                "criterioId": cid,
                "nome": nome,
                "descricao": descricao,
                "ordem": len(itens_out) + 1,
                "eliminatorio": bool(bruto.eliminatorio),
            }
        )
    parece = any(parece_regra_dura(i["nome"], i["descricao"]) for i in itens_out)
    if parece and not body.confirmarRegraDura:
        return {
            "precisaConfirmacao": True,
            "aviso": (
                "Este critério parece repetir regra já aplicada na triagem e não será usado "
                "pelo modelo como porta de entrada."
            ),
            "itens": itens_out,
        }
    versao = salvar_criterios_qual(db, projeto, itens_out)
    return {"versaoId": versao.id, "itens": versao.itens, "avisos": avisos}


@router.get("/{projeto_id}/prompt")
def get_prompt(projeto_id: str, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    vigente = prompt_vigente(db, projeto)
    versoes = [
        {
            "promptId": p.prompt_id,
            "versao": p.versao,
            "criadoEm": p.criado_em.isoformat() if p.criado_em else None,
            "criteriosQualitativosVersaoId": p.criterios_qualitativos_versao_id,
            "template": p.template,
        }
        for p in listar_prompts(db, projeto.id)
    ]
    return {
        "vigente": None
        if vigente is None
        else {
            "promptId": vigente.prompt_id,
            "versao": vigente.versao,
            "template": vigente.template,
            "criteriosQualitativosVersaoId": vigente.criterios_qualitativos_versao_id,
            "criadoEm": vigente.criado_em.isoformat() if vigente.criado_em else None,
        },
        "templateInicial": TEMPLATE_INICIAL,
        "versoes": versoes,
    }


@router.put("/{projeto_id}/prompt")
def put_prompt(projeto_id: str, body: PromptIn, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    erro = validar_template(body.template)
    if erro:
        raise HTTPException(status_code=400, detail=erro)
    qual = criterios_qual_vigentes(db, projeto.id)
    if qual is None or not qual.itens:
        raise HTTPException(status_code=400, detail="Cadastre ao menos um critério qualitativo da vaga.")
    row = salvar_prompt(db, projeto, body.template, qual)
    return {
        "promptId": row.prompt_id,
        "versao": row.versao,
        "template": row.template,
        "criteriosQualitativosVersaoId": row.criterios_qualitativos_versao_id,
        "criadoEm": row.criado_em.isoformat() if row.criado_em else None,
    }


@router.post("/{projeto_id}/prompt/preview")
def post_preview(projeto_id: str, body: PreviewIn, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    vigente = prompt_vigente(db, projeto)
    template = vigente.template if vigente else TEMPLATE_INICIAL
    itens = (vigente.criterios_embutidos_snapshot if vigente else None) or []
    if not itens:
        qual = criterios_qual_vigentes(db, projeto.id)
        itens = [] if qual is None else qual.itens
    candidatos = [candidato_para_dict(c) for c in listar_candidatos(db, projeto.id)]
    decisoes = decisoes_por_candidato(db, projeto.id)
    elegiveis = [
        c
        for c in candidatos
        if (decisoes.get(c["candidatoId"]) and decisoes[c["candidatoId"]].resultado == "elegivel")
        and resposta_utilizavel(c.get("respostasChatbot"))
    ]
    if not elegiveis:
        return {
            "texto": "",
            "mensagem": "Não há candidato com resposta utilizável para montar o texto.",
        }
    escolhido = next((c for c in elegiveis if c["candidatoId"] == body.candidatoId), elegiveis[0])
    texto = montar_preview(template, escolhido["candidatoId"], itens, escolhido.get("respostasChatbot") or [])
    return {
        "candidatoId": escolhido["candidatoId"],
        "texto": texto,
        "candidatos": [
            {"candidatoId": c["candidatoId"], "nomeExibicao": c.get("nomeExibicao"), "linhaOrigem": c["linhaOrigem"]}
            for c in elegiveis
        ],
    }


def _envelope(cand: dict, decisao, avaliacao) -> dict:
    base = {
        "candidatoId": cand["candidatoId"],
        "linhaOrigem": cand["linhaOrigem"],
        "nomeExibicao": cand.get("nomeExibicao"),
        "ultimoCargo": cand.get("ultimoCargo"),
        "idade": cand.get("idade"),
        "escolaridade": cand.get("escolaridade"),
        "temRespostaUtilizavel": resposta_utilizavel(cand.get("respostasChatbot")),
    }
    if decisao is None:
        return {**base, "resultadoExibicao": "sem_triagem", "decisao": None, "avaliacao": None}
    d = {
        "resultado": decisao.resultado,
        "motivos": decisao.motivos,
        "criteriosInativos": decisao.criterios_inativos,
        "criteriosVersao": decisao.criterios_versao,
    }
    if decisao.resultado == "inelegivel":
        return {**base, "resultadoExibicao": "inelegivel", "decisao": d, "avaliacao": None}
    if not resposta_utilizavel(cand.get("respostasChatbot")):
        return {**base, "resultadoExibicao": "aguardando_resposta", "decisao": d, "avaliacao": None}
    if avaliacao is None:
        return {**base, "resultadoExibicao": "elegivel_pendente_ia", "decisao": d, "avaliacao": None}
    av = {
        "promptVersionId": avaliacao.prompt_version_id,
        "criteriosQualitativosVersaoId": avaliacao.criterios_qualitativos_versao_id,
        "perfil": avaliacao.perfil,
        "compatibilidade": avaliacao.compatibilidade,
        "justificativasPorCriterio": avaliacao.justificativas_por_criterio,
        "usoToken": avaliacao.uso_token,
        "estado": avaliacao.estado,
        "erro": avaliacao.erro,
        "criadoEm": avaliacao.criado_em.isoformat() if avaliacao.criado_em else None,
    }
    if avaliacao.estado == "sucesso":
        return {**base, "resultadoExibicao": "avaliado", "decisao": d, "avaliacao": av}
    return {**base, "resultadoExibicao": "falha_avaliacao", "decisao": d, "avaliacao": av}


@router.get("/{projeto_id}/resultado")
def get_resultado(projeto_id: str, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    candidatos = [candidato_para_dict(c) for c in listar_candidatos(db, projeto.id)]
    decisoes = decisoes_por_candidato(db, projeto.id)
    linhas = []
    for cand in candidatos:
        av = avaliacao_mais_recente(db, projeto.id, cand["candidatoId"])
        linhas.append(_envelope(cand, decisoes.get(cand["candidatoId"]), av))
    return {
        "linhas": linhas,
        "pedidoTrajetoria": PEDIDO_TRAJETORIA,
        "llm": {
            "configurada": config.llm_configurada(),
            "modelo": config.llm_model(),
            "baseUrlDefinida": bool(config.llm_base_url()),
        },
    }


@router.get("/{projeto_id}/avaliacao-ia/lote")
def get_lote(projeto_id: str, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    candidatos = [candidato_para_dict(c) for c in listar_candidatos(db, projeto.id)]
    decisoes = decisoes_por_candidato(db, projeto.id)
    linhas = []
    for cand in candidatos:
        av = avaliacao_mais_recente(db, projeto.id, cand["candidatoId"])
        env = _envelope(cand, decisoes.get(cand["candidatoId"]), av)
        selecionavel = env["resultadoExibicao"] in {"elegivel_pendente_ia", "avaliado", "falha_avaliacao"}
        linhas.append({**env, "selecionavel": selecionavel, "incluidoPadrao": selecionavel})
    vigente = prompt_vigente(db, projeto)
    qual = criterios_qual_vigentes(db, projeto.id)
    faltas: list[str] = []
    mapa = projeto.mapeamento_colunas or {}
    if not (mapa.get("respostasChatbot") or []):
        faltas.append(
            "Mapeie ao menos uma coluna de resposta do chatbot na importação. Sem esse mapeamento a avaliação por IA não roda."
        )
    if qual is None or not qual.itens:
        faltas.append("Cadastre ao menos um critério qualitativo da vaga.")
    if vigente is None:
        faltas.append("Salve um prompt do projeto antes de avaliar.")
    elif qual is not None and vigente.criterios_qualitativos_versao_id != qual.id:
        faltas.append(
            "Os critérios qualitativos mudaram desde a última versão salva do prompt. "
            "Salve o prompt para gerar uma versão com os critérios atuais antes de avaliar."
        )
    if not config.llm_configurada():
        faltas.append(
            "A avaliação por IA não está configurada. Defina as variáveis de ambiente do modelo "
            "(a chave não aparece nesta tela)."
        )
    return {
        "linhas": linhas,
        "faltas": faltas,
        "llm": {
            "configurada": config.llm_configurada(),
            "modelo": config.llm_model(),
            "baseUrlDefinida": bool(config.llm_base_url()),
        },
        "pedidoTrajetoria": PEDIDO_TRAJETORIA,
    }


@router.post("/{projeto_id}/avaliacao-ia/executar")
def post_avaliar(projeto_id: str, body: AvaliarIn, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    try:
        recusar_se_nao_configurado()
    except RecusaLote as exc:
        raise HTTPException(status_code=400, detail=exc.mensagem) from exc
    if not body.confirmar:
        raise HTTPException(
            status_code=400,
            detail="Confirme o envio. Esta execução envia N candidato(s) ao modelo, um por chamada. "
            "Quem está inelegível, aguardando resposta ou desmarcado não será enviado.",
        )
    candidatos = {c["candidatoId"]: c for c in (candidato_para_dict(x) for x in listar_candidatos(db, projeto.id))}
    decisoes_rows = decisoes_por_candidato(db, projeto.id)
    decisoes = {
        cid: {
            "resultado": row.resultado,
            "motivos": row.motivos,
            "criteriosInativos": row.criterios_inativos,
        }
        for cid, row in decisoes_rows.items()
    }
    vigente = prompt_vigente(db, projeto)
    qual = criterios_qual_vigentes(db, projeto.id)
    if vigente is None:
        raise HTTPException(status_code=400, detail="Salve um prompt do projeto antes de avaliar.")
    if qual is None:
        raise HTTPException(status_code=400, detail="Cadastre ao menos um critério qualitativo da vaga.")
    try:
        saida = avaliar_lote(
            candidatos_por_id=candidatos,
            decisoes_por_id=decisoes,
            ids_selecionados=body.candidatoIds,
            template=vigente.template,
            prompt_id=vigente.prompt_id,
            criterios_prompt_versao_id=vigente.criterios_qualitativos_versao_id,
            criterios_vigente_id=qual.id,
            itens_embutidos=vigente.criterios_embutidos_snapshot,
            mapeamento=projeto.mapeamento_colunas,
        )
    except RecusaLote as exc:
        raise HTTPException(status_code=400, detail=exc.mensagem) from exc
    persistidos = []
    soma_ent = 0
    soma_sai = 0
    soma_tot = 0
    sem_uso = 0
    for r in saida["resultados"]:
        gravar_avaliacao(db, projeto, r)
        persistidos.append(
            {
                "candidatoId": r["candidatoId"],
                "estado": r["estado"],
                "compatibilidade": r.get("compatibilidade"),
                "erro": r.get("erro"),
            }
        )
        uso = r.get("usoToken") or {}
        if uso.get("total") is None:
            sem_uso += 1
        else:
            soma_ent += int(uso.get("entrada") or 0)
            soma_sai += int(uso.get("saida") or 0)
            soma_tot += int(uso.get("total") or 0)
    return {
        "enviados": saida["enviados"],
        "resultados": persistidos,
        "tokens": {
            "entrada": soma_ent,
            "saida": soma_sai,
            "total": soma_tot,
            "registrosSemUso": sem_uso,
        },
    }


