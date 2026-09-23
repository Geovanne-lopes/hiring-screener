"""Adaptador HTTP estilo OpenAI. Sem fornecedor fixo no código."""

from __future__ import annotations

import time
from typing import Any, Protocol

import httpx

import config


class ClienteLLM(Protocol):
    def completar(self, mensagens: list[dict[str, str]]) -> dict[str, Any]:
        """Retorna {conteudo, uso, status} ou levanta ErroClienteLLM."""


class ErroClienteLLM(Exception):
    def __init__(self, codigo: str, mensagem: str) -> None:
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


class ClienteOpenAICompat:
    def __init__(self) -> None:
        self.base_url = config.llm_base_url().rstrip("/")
        self.api_key = config.llm_api_key()
        self.model = config.llm_model()
        self.timeout = config.llm_timeout_seconds()
        self.max_retries = config.llm_max_retries()

    def completar(self, mensagens: list[dict[str, str]]) -> dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": mensagens,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        tentativas_rede = 0
        espera = 1.0
        ultima: Exception | None = None
        max_tentativas = 1 + max(0, self.max_retries)
        while tentativas_rede < max_tentativas:
            tentativas_rede += 1
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json=payload, headers=headers)
                if resp.status_code == 429:
                    codigo_api = ""
                    try:
                        codigo_api = str((resp.json().get("error") or {}).get("code") or "")
                    except Exception:
                        codigo_api = ""
                    if codigo_api in ("insufficient_quota", "credit_balance_exhausted"):
                        raise ErroClienteLLM(
                            "sem_credito",
                            "A conta do modelo está sem cota ou sem créditos. Troque a chave ou recarregue o saldo para avaliar.",
                        )
                    ultima = ErroClienteLLM("falha_rede", f"HTTP {resp.status_code}")
                    if tentativas_rede < max_tentativas:
                        time.sleep(espera)
                        espera = 2.0
                        continue
                    raise ErroClienteLLM("falha_rede", f"HTTP {resp.status_code} após retries.")
                if resp.status_code in (401, 403):
                    raise ErroClienteLLM("erro_http", "Chave inválida ou recusada pelo provedor.")
                if resp.status_code == 400:
                    raise ErroClienteLLM("erro_http", "HTTP 400 da API do modelo.")
                if resp.status_code >= 400:
                    raise ErroClienteLLM("erro_http", f"HTTP {resp.status_code}.")
                corpo = resp.json()
                escolha = (corpo.get("choices") or [{}])[0]
                conteudo = ((escolha.get("message") or {}).get("content")) or ""
                uso = corpo.get("usage") or {}
                return {
                    "conteudo": conteudo,
                    "uso": _mapear_uso(uso),
                    "tentativasRede": tentativas_rede,
                }
            except ErroClienteLLM:
                raise
            except httpx.TimeoutException as exc:
                ultima = ErroClienteLLM("timeout", "Timeout na chamada ao modelo.")
                if tentativas_rede < max_tentativas:
                    time.sleep(espera)
                    espera = 2.0
                    continue
                raise ErroClienteLLM("timeout", "Timeout esgotado.") from exc
            except httpx.HTTPError as exc:
                ultima = ErroClienteLLM("falha_rede", "Falha de rede na chamada ao modelo.")
                if tentativas_rede < max_tentativas:
                    time.sleep(espera)
                    espera = 2.0
                    continue
                raise ErroClienteLLM("falha_rede", "Falha de rede esgotada.") from exc
        if ultima:
            raise ultima
        raise ErroClienteLLM("falha_rede", "Falha de rede.")


def _mapear_uso(uso: dict) -> dict[str, int | None]:
    entrada = uso.get("prompt_tokens")
    saida = uso.get("completion_tokens")
    total = uso.get("total_tokens")
    if entrada is None and saida is None and total is None:
        return {"entrada": None, "saida": None, "total": None, "nota": "uso_nao_reportado"}
    return {"entrada": entrada, "saida": saida, "total": total, "nota": None}


_cliente_padrao: ClienteLLM | None = None


def cliente_padrao() -> ClienteLLM:
    global _cliente_padrao
    if _cliente_padrao is None:
        _cliente_padrao = ClienteOpenAICompat()
    return _cliente_padrao
