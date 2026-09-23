from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from persistencia.db import Base


def agora() -> datetime:
    return datetime.now().astimezone()


class Projeto(Base):
    __tablename__ = "projetos"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    mapeamento_colunas: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    prompt_vigente_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    criterios_det_vigente_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    criterios_qual_vigente_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class CriteriosDeterministicosVersao(Base):
    __tablename__ = "criterios_deterministicos"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    projeto_id: Mapped[str] = mapped_column(ForeignKey("projetos.id"), nullable=False, index=True)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class CandidatoImportado(Base):
    __tablename__ = "candidatos"

    candidato_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    projeto_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    linha_origem: Mapped[int] = mapped_column(Integer, nullable=False)
    ultimo_cargo: Mapped[str | None] = mapped_column(Text, nullable=True)
    idade: Mapped[str | None] = mapped_column(Text, nullable=True)
    escolaridade: Mapped[str | None] = mapped_column(Text, nullable=True)
    nome_exibicao: Mapped[str | None] = mapped_column(Text, nullable=True)
    telefone: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    busca_lkd: Mapped[str | None] = mapped_column(Text, nullable=True)
    cidade: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_legado: Mapped[str | None] = mapped_column(Text, nullable=True)
    respostas_chatbot: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


class DecisaoTriagem(Base):
    __tablename__ = "decisoes_triagem"

    candidato_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    projeto_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    resultado: Mapped[str] = mapped_column(String(32), nullable=False)
    motivos: Mapped[list] = mapped_column(JSON, nullable=False)
    criterios_inativos: Mapped[list] = mapped_column(JSON, nullable=False)
    criterios_versao: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_criterios: Mapped[dict] = mapped_column(JSON, nullable=False)


class CriteriosQualitativosVersao(Base):
    __tablename__ = "criterios_qualitativos"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    projeto_id: Mapped[str] = mapped_column(ForeignKey("projetos.id"), nullable=False, index=True)
    itens: Mapped[list] = mapped_column(JSON, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class PromptDoProjeto(Base):
    __tablename__ = "prompts"

    prompt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    versao: Mapped[int] = mapped_column(Integer, nullable=False)
    projeto_id: Mapped[str] = mapped_column(ForeignKey("projetos.id"), nullable=False, index=True)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    criterios_qualitativos_versao_id: Mapped[str] = mapped_column(String(64), nullable=False)
    criterios_embutidos_snapshot: Mapped[list] = mapped_column(JSON, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class AvaliacaoIa(Base):
    __tablename__ = "avaliacoes_ia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidato_id: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    projeto_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    prompt_version_id: Mapped[str] = mapped_column(String(64), nullable=False)
    criterios_qualitativos_versao_id: Mapped[str] = mapped_column(String(64), nullable=False)
    perfil: Mapped[str | None] = mapped_column(Text, nullable=True)
    compatibilidade: Mapped[str | None] = mapped_column(String(32), nullable=True)
    justificativas_por_criterio: Mapped[list | None] = mapped_column(JSON, nullable=True)
    uso_token: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    estado: Mapped[str] = mapped_column(String(32), nullable=False)
    erro: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class RegistroChamada(Base):
    __tablename__ = "registros_chamada"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidato_id: Mapped[str] = mapped_column(String(96), nullable=False)
    projeto_id: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version_id: Mapped[str] = mapped_column(String(64), nullable=False)
    modelo_configurado: Mapped[str] = mapped_column(String(255), nullable=False)
    tokens_entrada: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_saida: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nota_uso: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status_chamada: Mapped[str] = mapped_column(String(32), nullable=False)
    tentativas_rede: Mapped[int] = mapped_column(Integer, nullable=False)
    houve_reparo_json: Mapped[bool] = mapped_column(nullable=False, default=False)
    compatibilidade_modelo: Mapped[str | None] = mapped_column(String(32), nullable=True)
    compatibilidade_calculada: Mapped[str | None] = mapped_column(String(32), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
