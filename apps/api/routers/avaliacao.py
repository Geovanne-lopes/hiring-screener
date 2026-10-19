from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import config
from avaliacao_ia.exportar import planilha_resultado
from avaliacao_ia.ranking import atribuir_posicoes, media_meio_para_cima
from avaliacao_ia.prompt import (
    MSG_JOB_DESCRIPTION_DESALINHADA,
    MSG_PROMPT_SEM_JOB,
    TEMPLATE_INICIAL,
    parece_regra_dura,
    template_e_antigo,
    validar_template,
)
from avaliacao_ia.validacao import rotulo_resultado
from avaliacao_ia.resposta import resposta_utilizavel
from avaliacao_ia.servico import RecusaLote, avaliar_lote, montar_preview, recusar_se_nao_configurado
from persistencia.db import get_db
from persistencia.repositorio import (
    avaliacao_mais_recente,
    candidato_para_dict,
    criterios_qual_vigentes,
    decisoes_por_candidato,
    gravar_avaliacao,
    job_description_vigente,
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
            "jobDescriptionVersaoId": p.job_description_versao_id,
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
            "jobDescriptionVersaoId": vigente.job_description_versao_id,
            "jobDescriptionSnapshot": vigente.job_description_snapshot,
            "criadoEm": vigente.criado_em.isoformat() if vigente.criado_em else None,
        },
        "templateInicial": TEMPLATE_INICIAL,
        "modeloRevisao": TEMPLATE_INICIAL,
        "templateAntigo": template_e_antigo(None if vigente is None else vigente.template),
        "versoes": versoes,
    }


@router.put("/{projeto_id}/prompt")
def put_prompt(projeto_id: str, body: PromptIn, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    erro = validar_template(body.template)
    if erro:
        raise HTTPException(status_code=400, detail=erro)
    jd = job_description_vigente(db, projeto.id)
    if jd is None or not (jd.texto or "").strip():
        raise HTTPException(status_code=400, detail=MSG_PROMPT_SEM_JOB)
    row = salvar_prompt(db, projeto, body.template, jd)
    return {
        "promptId": row.prompt_id,
        "versao": row.versao,
        "template": row.template,
        "criteriosQualitativosVersaoId": row.criterios_qualitativos_versao_id,
        "jobDescriptionVersaoId": row.job_description_versao_id,
        "jobDescriptionSnapshot": row.job_description_snapshot,
        "criadoEm": row.criado_em.isoformat() if row.criado_em else None,
    }


@router.post("/{projeto_id}/prompt/preview")
def post_preview(projeto_id: str, body: PreviewIn, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    vigente = prompt_vigente(db, projeto)
    template = vigente.template if vigente else TEMPLATE_INICIAL
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
    jd = job_description_vigente(db, projeto.id)
    texto_jd = "" if jd is None else jd.texto
    texto = montar_preview(
        template,
        escolhido["candidatoId"],
        escolhido.get("respostasChatbot") or [],
        texto_jd,
    )
    return {
        "candidatoId": escolhido["candidatoId"],
        "texto": texto,
        "candidatos": [
            {"candidatoId": c["candidatoId"], "nomeExibicao": c.get("nomeExibicao"), "linhaOrigem": c["linhaOrigem"]}
            for c in elegiveis
        ],
    }


def _por_pergunta_publico(avaliacao) -> list[dict] | None:
    bruto = avaliacao.por_pergunta
    if bruto is None:
        return None
    trechos = {
        item.get("perguntaId"): item.get("trecho") or ""
        for item in (avaliacao.trechos or [])
        if isinstance(item, dict)
    }
    saida = []
    for item in bruto:
        if not isinstance(item, dict):
            continue
        resultado = item.get("resultado") or ""
        saida.append(
            {
                "perguntaId": item.get("perguntaId"),
                "pergunta": item.get("pergunta"),
                "resultado": resultado,
                "justificativa": item.get("justificativa") or "",
                "trecho": trechos.get(item.get("perguntaId"), ""),
                "rotulo": rotulo_resultado(resultado),
            }
        )
    return saida


def _avaliacao_publica(avaliacao) -> dict:
    por_pergunta = _por_pergunta_publico(avaliacao)
    schema_novo = por_pergunta is not None
    return {
        "promptVersionId": avaliacao.prompt_version_id,
        "jobDescriptionVersaoId": avaliacao.job_description_versao_id,
        "perfil": avaliacao.perfil,
        "compatibilidade": None if schema_novo else avaliacao.compatibilidade,
        "justificativasPorCriterio": None if schema_novo else avaliacao.justificativas_por_criterio,
        "porPergunta": por_pergunta,
        "trechos": avaliacao.trechos if schema_novo else None,
        "notaTecnica": avaliacao.nota_tecnica if schema_novo else None,
        "notaComportamental": avaliacao.nota_comportamental if schema_novo else None,
        "justificativaNotaTecnica": avaliacao.justificativa_nota_tecnica if schema_novo else None,
        "justificativaNotaComportamental": avaliacao.justificativa_nota_comportamental if schema_novo else None,
        "schema": "por_pergunta" if schema_novo else "legado",
        "usoToken": avaliacao.uso_token,
        "estado": avaliacao.estado,
        "erro": avaliacao.erro,
        "criadoEm": avaliacao.criado_em.isoformat() if avaliacao.criado_em else None,
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
    av = _avaliacao_publica(avaliacao)
    if avaliacao.estado == "sucesso":
        return {**base, "resultadoExibicao": "avaliado", "decisao": d, "avaliacao": av}
    return {**base, "resultadoExibicao": "falha_avaliacao", "decisao": d, "avaliacao": av}


def _entrada_ranking(cand: dict, avaliacao) -> dict | None:
    if avaliacao is None or avaliacao.estado != "sucesso" or avaliacao.por_pergunta is None:
        return None
    if avaliacao.nota_tecnica is None or avaliacao.nota_comportamental is None:
        return None
    final = avaliacao.nota_final
    if final is None:
        final = media_meio_para_cima(avaliacao.nota_tecnica, avaliacao.nota_comportamental)
    return {
        "candidatoId": cand["candidatoId"],
        "linhaOrigem": cand["linhaOrigem"],
        "notaTecnica": avaliacao.nota_tecnica,
        "notaComportamental": avaliacao.nota_comportamental,
        "notaFinal": final,
        "zerada": bool(avaliacao.nota_tecnica_zerada_por_falta_de_informacao),
    }


def _linhas_resultado(db: Session, projeto_id: str) -> list[dict]:
    candidatos = [candidato_para_dict(c) for c in listar_candidatos(db, projeto_id)]
    decisoes = decisoes_por_candidato(db, projeto_id)
    pares = []
    entradas = []
    for cand in candidatos:
        av = avaliacao_mais_recente(db, projeto_id, cand["candidatoId"])
        pares.append((cand, decisoes.get(cand["candidatoId"]), av))
        entrada = _entrada_ranking(cand, av)
        if entrada is not None:
            entradas.append(entrada)
    posicoes = atribuir_posicoes(entradas)
    final_por_id = {item["candidatoId"]: item["notaFinal"] for item in entradas}
    zerada_por_id = {item["candidatoId"]: item["zerada"] for item in entradas}
    total = len(entradas)
    linhas = []
    for cand, decisao, av in pares:
        linha = _envelope(cand, decisao, av)
        cid = cand["candidatoId"]
        pos = posicoes.get(cid)
        linha["ranking"] = {
            "notaFinal": final_por_id.get(cid),
            "notaTecnicaZeradaPorFaltaDeInformacao": bool(zerada_por_id.get(cid, False)),
            "posicaoTecnica": None if pos is None else pos["posicaoTecnica"],
            "posicaoComportamental": None if pos is None else pos["posicaoComportamental"],
            "posicaoFinal": None if pos is None else pos["posicaoFinal"],
            "totalComNota": total,
        }
        linhas.append(linha)
    return linhas


@router.get("/{projeto_id}/resultado")
def get_resultado(projeto_id: str, db: Session = Depends(get_db)):
    projeto = _exige(db, projeto_id)
    return {
        "linhas": _linhas_resultado(db, projeto.id),
        "pedidoTrajetoria": PEDIDO_TRAJETORIA,
        "llm": {
            "configurada": config.llm_configurada(),
            "modelo": config.llm_model(),
            "baseUrlDefinida": bool(config.llm_base_url()),
        },
    }


@router.get("/{projeto_id}/resultado/exportar")
def exportar_resultado(
    projeto_id: str,
    so_com_nota: bool = Query(False, alias="soComNota"),
    db: Session = Depends(get_db),
):
    projeto = _exige(db, projeto_id)
    candidatos = listar_candidatos(db, projeto.id)
    if not candidatos:
        raise HTTPException(status_code=400, detail="Importe uma planilha antes de exportar o resultado.")
    linhas = _linhas_resultado(db, projeto.id)
    if so_com_nota:
        linhas = [linha for linha in linhas if (linha.get("ranking") or {}).get("posicaoFinal") is not None]
    contatos = {
        cand.candidato_id: {
            "nome": cand.nome_exibicao or "",
            "email": cand.email or "",
            "telefone": cand.telefone or "",
        }
        for cand in candidatos
    }
    conteudo = planilha_resultado(linhas, contatos)
    nome = "".join(ch if ch.isalnum() or ch in " -_" else "_" for ch in projeto.nome).strip() or "resultado"
    arquivo = f"resultado-{nome}.xlsx"
    return Response(
        content=conteudo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(arquivo)}"},
    )


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
    faltas: list[str] = []
    mapa = projeto.mapeamento_colunas or {}
    if not (mapa.get("respostasChatbot") or []):
        faltas.append(
            "Mapeie ao menos uma coluna de resposta do chatbot na importação. Sem esse mapeamento a avaliação por IA não roda."
        )
    if vigente is None:
        faltas.append("Salve um prompt do projeto antes de avaliar.")
    else:
        erro_template = validar_template(vigente.template or "")
        if erro_template:
            faltas.append(erro_template)
        jd = job_description_vigente(db, projeto.id)
        jd_id = None if jd is None else jd.id
        if not jd_id or vigente.job_description_versao_id != jd_id or not (vigente.job_description_snapshot or "").strip():
            faltas.append(MSG_JOB_DESCRIPTION_DESALINHADA)
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
    jd = job_description_vigente(db, projeto.id)
    if vigente is None:
        raise HTTPException(status_code=400, detail="Salve um prompt do projeto antes de avaliar.")
    try:
        saida = avaliar_lote(
            candidatos_por_id=candidatos,
            decisoes_por_id=decisoes,
            ids_selecionados=body.candidatoIds,
            template=vigente.template,
            prompt_id=vigente.prompt_id,
            mapeamento=projeto.mapeamento_colunas,
            job_description_snapshot=vigente.job_description_snapshot or "",
            job_description_versao_id=vigente.job_description_versao_id,
            job_description_vigente_id=None if jd is None else jd.id,
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


