from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from persistencia.models import (
    AvaliacaoIa,
    CandidatoImportado,
    CriteriosDeterministicosVersao,
    CriteriosQualitativosVersao,
    DecisaoTriagem,
    PromptDoProjeto,
    Projeto,
    RegistroChamada,
    agora,
)
from triagem.avaliar import criterios_iniciais


def novo_id(prefixo: str) -> str:
    return f"{prefixo}_{uuid.uuid4().hex[:10]}"


def listar_projetos(db: Session) -> list[Projeto]:
    return list(db.scalars(select(Projeto).order_by(Projeto.atualizado_em.desc())))


def obter_projeto(db: Session, projeto_id: str) -> Projeto | None:
    return db.get(Projeto, projeto_id)


def criar_projeto(db: Session, nome: str) -> Projeto:
    projeto = Projeto(id=novo_id("prj"), nome=nome.strip(), criado_em=agora(), atualizado_em=agora())
    db.add(projeto)
    db.flush()
    versao = _nova_versao_det(db, projeto.id, criterios_iniciais())
    projeto.criterios_det_vigente_id = versao.id
    projeto.atualizado_em = agora()
    db.commit()
    db.refresh(projeto)
    return projeto


def renomear_projeto(db: Session, projeto: Projeto, nome: str) -> Projeto:
    projeto.nome = nome.strip()
    projeto.atualizado_em = agora()
    db.commit()
    db.refresh(projeto)
    return projeto


def duplicar_projeto(db: Session, origem: Projeto, nome: str) -> Projeto:
    snapshot = criterios_det_vigentes(db, origem.id) or criterios_iniciais()
    novo = Projeto(id=novo_id("prj"), nome=nome.strip(), criado_em=agora(), atualizado_em=agora())
    db.add(novo)
    db.flush()
    versao = _nova_versao_det(db, novo.id, snapshot)
    novo.criterios_det_vigente_id = versao.id
    db.commit()
    db.refresh(novo)
    return novo


def _proxima_versao(db: Session, modelo, projeto_id: str, prefixo: str) -> str:
    qtd = db.scalar(select(func.count()).select_from(modelo).where(modelo.projeto_id == projeto_id)) or 0
    return f"{prefixo}_{projeto_id}_{qtd + 1:02d}"


def _nova_versao_det(db: Session, projeto_id: str, snapshot: dict) -> CriteriosDeterministicosVersao:
    versao = CriteriosDeterministicosVersao(
        id=_proxima_versao(db, CriteriosDeterministicosVersao, projeto_id, "crt_det"),
        projeto_id=projeto_id,
        snapshot=snapshot,
        criado_em=agora(),
    )
    db.add(versao)
    db.flush()
    return versao


def criterios_det_vigentes(db: Session, projeto_id: str) -> dict | None:
    projeto = obter_projeto(db, projeto_id)
    if not projeto or not projeto.criterios_det_vigente_id:
        return None
    row = db.get(CriteriosDeterministicosVersao, projeto.criterios_det_vigente_id)
    return None if row is None else row.snapshot


def salvar_criterios_det(db: Session, projeto: Projeto, snapshot: dict) -> CriteriosDeterministicosVersao:
    versao = _nova_versao_det(db, projeto.id, snapshot)
    projeto.criterios_det_vigente_id = versao.id
    projeto.atualizado_em = agora()
    db.commit()
    db.refresh(versao)
    return versao


def substituir_lote(db: Session, projeto: Projeto, mapeamento: dict, candidatos: list[dict]) -> None:
    db.query(AvaliacaoIa).filter(AvaliacaoIa.projeto_id == projeto.id).delete()
    db.query(RegistroChamada).filter(RegistroChamada.projeto_id == projeto.id).delete()
    db.query(DecisaoTriagem).filter(DecisaoTriagem.projeto_id == projeto.id).delete()
    db.query(CandidatoImportado).filter(CandidatoImportado.projeto_id == projeto.id).delete()
    for cand in candidatos:
        db.add(
            CandidatoImportado(
                candidato_id=cand["candidatoId"],
                projeto_id=projeto.id,
                linha_origem=cand["linhaOrigem"],
                ultimo_cargo=cand.get("ultimoCargo"),
                idade=cand.get("idade"),
                escolaridade=cand.get("escolaridade"),
                nome_exibicao=cand.get("nomeExibicao"),
                telefone=cand.get("telefone"),
                email=cand.get("email"),
                busca_lkd=cand.get("buscaLkd"),
                cidade=cand.get("cidade"),
                status_legado=cand.get("statusLegado"),
                respostas_chatbot=cand.get("respostasChatbot") or [],
            )
        )
    projeto.mapeamento_colunas = mapeamento
    projeto.atualizado_em = agora()
    db.commit()


def listar_candidatos(db: Session, projeto_id: str) -> list[CandidatoImportado]:
    return list(
        db.scalars(
            select(CandidatoImportado)
            .where(CandidatoImportado.projeto_id == projeto_id)
            .order_by(CandidatoImportado.linha_origem)
        )
    )


def candidato_para_dict(row: CandidatoImportado) -> dict:
    return {
        "candidatoId": row.candidato_id,
        "projetoId": row.projeto_id,
        "linhaOrigem": row.linha_origem,
        "ultimoCargo": row.ultimo_cargo,
        "idade": row.idade,
        "escolaridade": row.escolaridade,
        "nomeExibicao": row.nome_exibicao,
        "telefone": row.telefone,
        "email": row.email,
        "buscaLkd": row.busca_lkd,
        "cidade": row.cidade,
        "statusLegado": row.status_legado,
        "respostasChatbot": row.respostas_chatbot or [],
    }


def substituir_decisoes(db: Session, projeto: Projeto, decisoes: list[dict], snapshot: dict, versao_id: str) -> None:
    db.query(DecisaoTriagem).filter(DecisaoTriagem.projeto_id == projeto.id).delete()
    for d in decisoes:
        db.add(
            DecisaoTriagem(
                candidato_id=d["candidatoId"],
                projeto_id=projeto.id,
                resultado=d["resultado"],
                motivos=d["motivos"],
                criterios_inativos=d["criteriosInativos"],
                criterios_versao=versao_id,
                snapshot_criterios=snapshot,
            )
        )
    projeto.atualizado_em = agora()
    db.commit()


def decisoes_por_candidato(db: Session, projeto_id: str) -> dict[str, DecisaoTriagem]:
    rows = db.scalars(select(DecisaoTriagem).where(DecisaoTriagem.projeto_id == projeto_id)).all()
    return {r.candidato_id: r for r in rows}


def criterios_qual_vigentes(db: Session, projeto_id: str) -> CriteriosQualitativosVersao | None:
    projeto = obter_projeto(db, projeto_id)
    if not projeto or not projeto.criterios_qual_vigente_id:
        return None
    return db.get(CriteriosQualitativosVersao, projeto.criterios_qual_vigente_id)


def salvar_criterios_qual(db: Session, projeto: Projeto, itens: list[dict]) -> CriteriosQualitativosVersao:
    versao = CriteriosQualitativosVersao(
        id=_proxima_versao(db, CriteriosQualitativosVersao, projeto.id, "crt_qual"),
        projeto_id=projeto.id,
        itens=itens,
        criado_em=agora(),
    )
    db.add(versao)
    db.flush()
    projeto.criterios_qual_vigente_id = versao.id
    projeto.atualizado_em = agora()
    db.commit()
    db.refresh(versao)
    return versao


def prompt_vigente(db: Session, projeto: Projeto) -> PromptDoProjeto | None:
    if not projeto.prompt_vigente_id:
        return None
    return db.get(PromptDoProjeto, projeto.prompt_vigente_id)


def listar_prompts(db: Session, projeto_id: str) -> list[PromptDoProjeto]:
    return list(
        db.scalars(
            select(PromptDoProjeto)
            .where(PromptDoProjeto.projeto_id == projeto_id)
            .order_by(PromptDoProjeto.versao.desc())
        )
    )


def salvar_prompt(db: Session, projeto: Projeto, template: str, qual: CriteriosQualitativosVersao) -> PromptDoProjeto:
    qtd = db.scalar(
        select(func.count()).select_from(PromptDoProjeto).where(PromptDoProjeto.projeto_id == projeto.id)
    ) or 0
    n = qtd + 1
    row = PromptDoProjeto(
        prompt_id=f"prm_{projeto.id}_{n:02d}",
        versao=n,
        projeto_id=projeto.id,
        template=template,
        criterios_qualitativos_versao_id=qual.id,
        criterios_embutidos_snapshot=qual.itens,
        criado_em=agora(),
    )
    db.add(row)
    db.flush()
    projeto.prompt_vigente_id = row.prompt_id
    projeto.atualizado_em = agora()
    db.commit()
    db.refresh(row)
    return row


def avaliacao_mais_recente(db: Session, projeto_id: str, candidato_id: str) -> AvaliacaoIa | None:
    return db.scalar(
        select(AvaliacaoIa)
        .where(AvaliacaoIa.projeto_id == projeto_id, AvaliacaoIa.candidato_id == candidato_id)
        .order_by(AvaliacaoIa.id.desc())
        .limit(1)
    )


def gravar_avaliacao(db: Session, projeto: Projeto, resultado: dict) -> AvaliacaoIa:
    uso = resultado.get("usoToken") or {}
    row = AvaliacaoIa(
        candidato_id=resultado["candidatoId"],
        projeto_id=projeto.id,
        prompt_version_id=resultado["promptVersionId"],
        criterios_qualitativos_versao_id=resultado["criteriosQualitativosVersaoId"],
        perfil=resultado.get("perfil"),
        compatibilidade=resultado.get("compatibilidade"),
        justificativas_por_criterio=resultado.get("justificativasPorCriterio"),
        uso_token=uso,
        estado=resultado["estado"],
        erro=resultado.get("erro"),
        criado_em=agora(),
    )
    db.add(row)
    db.add(
        RegistroChamada(
            candidato_id=resultado["candidatoId"],
            projeto_id=projeto.id,
            prompt_version_id=resultado["promptVersionId"],
            modelo_configurado=config_modelo(),
            tokens_entrada=uso.get("entrada"),
            tokens_saida=uso.get("saida"),
            tokens_total=uso.get("total"),
            nota_uso=resultado.get("notaUso"),
            status_chamada=resultado.get("statusChamada") or resultado["estado"],
            tentativas_rede=int(resultado.get("tentativasRede") or 0),
            houve_reparo_json=bool(resultado.get("houveReparoJson")),
            compatibilidade_modelo=resultado.get("compatibilidadeModelo"),
            compatibilidade_calculada=resultado.get("compatibilidade"),
            criado_em=agora(),
        )
    )
    projeto.atualizado_em = agora()
    db.commit()
    db.refresh(row)
    return row


def config_modelo() -> str:
    import config as cfg

    return cfg.llm_model()
