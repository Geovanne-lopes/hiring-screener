from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_API_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _API_DIR.parent.parent
load_dotenv(_REPO_ROOT / ".env")


def _caminho_db_padrao() -> str:
    return str(_REPO_ROOT / "data" / "screener.sqlite")


def db_path() -> str:
    bruto = os.environ.get("SCREENER_DB_PATH", "").strip()
    if not bruto:
        return _caminho_db_padrao()
    p = Path(bruto)
    if not p.is_absolute():
        p = (_REPO_ROOT / p).resolve()
    return str(p)


def llm_base_url() -> str:
    return os.environ.get("LLM_BASE_URL", "").strip()


def llm_api_key() -> str:
    return os.environ.get("LLM_API_KEY", "").strip()


def llm_model() -> str:
    return os.environ.get("LLM_MODEL", "").strip()


def llm_timeout_seconds() -> int:
    bruto = os.environ.get("LLM_TIMEOUT_SECONDS", "30").strip() or "30"
    try:
        return int(bruto)
    except ValueError:
        return 30


def llm_max_retries() -> int:
    bruto = os.environ.get("LLM_MAX_RETRIES", "2").strip() or "2"
    try:
        return int(bruto)
    except ValueError:
        return 2


def llm_configurada() -> bool:
    return bool(llm_api_key() and llm_base_url() and llm_model())
