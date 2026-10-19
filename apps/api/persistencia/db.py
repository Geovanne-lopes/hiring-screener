from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

import config


class Base(DeclarativeBase):
    pass


_engine = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def _engine_url() -> str:
    caminho = Path(config.db_path())
    caminho.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{caminho.as_posix()}"


def init_db() -> None:
    global _engine
    _engine = create_engine(_engine_url(), connect_args={"check_same_thread": False})
    SessionLocal.configure(bind=_engine)
    from persistencia import models as _models  # noqa: F401

    Base.metadata.create_all(bind=_engine)
    _garantir_colunas_contato(_engine)
    _garantir_colunas_job_description(_engine)
    _garantir_colunas_por_pergunta(_engine)
    _garantir_colunas_rankings(_engine)
    _garantir_colunas_justificativa_notas(_engine)


def _garantir_colunas_contato(engine) -> None:
    """create_all não adiciona coluna em tabela que já existe."""
    with engine.connect() as conn:
        existentes = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(candidatos)")}
        for nome in ("telefone", "email", "busca_lkd", "empresa"):
            if nome not in existentes:
                conn.exec_driver_sql(f"ALTER TABLE candidatos ADD COLUMN {nome} TEXT")
        conn.commit()


def _garantir_colunas_job_description(engine) -> None:
    """create_all não adiciona coluna em tabela que já existe."""

    def adicionar(conn, tabela: str, nome: str, tipo: str) -> None:
        existentes = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({tabela})")}
        if not existentes or nome in existentes:
            return
        conn.exec_driver_sql(f"ALTER TABLE {tabela} ADD COLUMN {nome} {tipo}")

    with engine.connect() as conn:
        adicionar(conn, "projetos", "job_description_vigente_id", "VARCHAR(64)")
        adicionar(conn, "prompts", "job_description_versao_id", "VARCHAR(64)")
        adicionar(conn, "prompts", "job_description_snapshot", "TEXT")
        adicionar(conn, "avaliacoes_ia", "job_description_versao_id", "VARCHAR(64)")
        conn.commit()


def _garantir_colunas_por_pergunta(engine) -> None:
    """create_all não adiciona coluna em tabela que já existe."""

    def adicionar(conn, tabela: str, nome: str, tipo: str) -> None:
        existentes = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({tabela})")}
        if not existentes or nome in existentes:
            return
        conn.exec_driver_sql(f"ALTER TABLE {tabela} ADD COLUMN {nome} {tipo}")

    with engine.connect() as conn:
        adicionar(conn, "avaliacoes_ia", "por_pergunta", "TEXT")
        adicionar(conn, "avaliacoes_ia", "trechos", "TEXT")
        adicionar(conn, "avaliacoes_ia", "nota_tecnica", "INTEGER")
        adicionar(conn, "avaliacoes_ia", "nota_comportamental", "INTEGER")
        conn.commit()


def _garantir_colunas_rankings(engine) -> None:
    """create_all não adiciona coluna em tabela que já existe."""

    def adicionar(conn, tabela: str, nome: str, tipo: str) -> None:
        existentes = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({tabela})")}
        if not existentes or nome in existentes:
            return
        conn.exec_driver_sql(f"ALTER TABLE {tabela} ADD COLUMN {nome} {tipo}")

    with engine.connect() as conn:
        adicionar(conn, "avaliacoes_ia", "nota_final", "INTEGER")
        adicionar(conn, "avaliacoes_ia", "nota_tecnica_zerada_por_falta_de_informacao", "INTEGER")
        conn.commit()


def _garantir_colunas_justificativa_notas(engine) -> None:
    """create_all não adiciona coluna em tabela que já existe."""

    def adicionar(conn, tabela: str, nome: str, tipo: str) -> None:
        existentes = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({tabela})")}
        if not existentes or nome in existentes:
            return
        conn.exec_driver_sql(f"ALTER TABLE {tabela} ADD COLUMN {nome} {tipo}")

    with engine.connect() as conn:
        adicionar(conn, "avaliacoes_ia", "justificativa_nota_tecnica", "TEXT")
        adicionar(conn, "avaliacoes_ia", "justificativa_nota_comportamental", "TEXT")
        conn.commit()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
