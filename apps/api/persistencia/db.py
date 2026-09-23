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


def _garantir_colunas_contato(engine) -> None:
    """create_all não adiciona coluna em tabela que já existe."""
    with engine.connect() as conn:
        existentes = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(candidatos)")}
        for nome in ("telefone", "email", "busca_lkd"):
            if nome not in existentes:
                conn.exec_driver_sql(f"ALTER TABLE candidatos ADD COLUMN {nome} TEXT")
        conn.commit()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
