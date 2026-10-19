"""Extrai texto de job description. Não chama LLM e não persiste."""

from __future__ import annotations

import io
from pathlib import Path

MSG_EXTENSAO = "Cole o texto ou envie um arquivo .txt, .md ou .docx."
MSG_UTF8 = "O arquivo não é UTF-8 válido. Escolha latin-1 ou cole o texto."
MSG_ENCODING = "Escolha utf-8 ou latin-1."
MSG_DOCX_SEM_TEXTO = "O arquivo .docx não tem texto nos parágrafos."
MSG_DOCX_INVALIDO = "Não foi possível ler o arquivo .docx. Cole o texto ou envie outro .docx."
MSG_VAZIA = "A job description está vazia."


class ErroJobDescription(ValueError):
    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem


def _codec(encoding: str) -> str:
    nome = (encoding or "utf-8").strip().lower()
    if nome in {"utf-8", "utf8"}:
        return "utf-8"
    if nome in {"latin-1", "latin1"}:
        return "latin-1"
    raise ErroJobDescription(MSG_ENCODING)


def _texto_docx(conteudo: bytes) -> str:
    from docx import Document

    try:
        doc = Document(io.BytesIO(conteudo))
    except Exception as exc:
        raise ErroJobDescription(MSG_DOCX_INVALIDO) from exc
    texto = "\n".join(paragrafo.text for paragrafo in doc.paragraphs)
    if not texto.strip():
        raise ErroJobDescription(MSG_DOCX_SEM_TEXTO)
    return texto


def extrair_texto(nome_arquivo: str, conteudo: bytes, encoding: str) -> str:
    extensao = Path(nome_arquivo or "").suffix.lower()
    if extensao == ".docx":
        return _texto_docx(conteudo)
    if extensao in {".txt", ".md"}:
        codec = _codec(encoding)
        try:
            return conteudo.decode(codec)
        except UnicodeDecodeError as exc:
            raise ErroJobDescription(MSG_UTF8) from exc
    raise ErroJobDescription(MSG_EXTENSAO)
