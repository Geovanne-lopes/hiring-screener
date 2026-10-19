"""Leitura de CSV/XLSX e identificação de linha. Sem triagem e sem LLM."""

from __future__ import annotations

import hashlib
import io
import re
from typing import Any

import pandas as pd

MSG_ARQUIVO_AUSENTE = "Selecione um arquivo CSV ou XLSX para importar."
MSG_SEM_CANDIDATOS = "O arquivo não contém linhas de candidato."
MSG_UTF8_INVALIDO = (
    "O arquivo não é UTF-8 válido. Tente o encoding latin-1 (caso típico do mapeamento legado)."
)
MSG_COLUNA_RESPOSTA_SEM_NOME = (
    "A coluna de resposta precisa de um nome, porque esse nome é a pergunta."
)

_UNNAMED = re.compile(r"^Unnamed: \d+$")


class ErroImportacao(ValueError):
    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem


def gerar_candidato_id(linha_origem: int, celulas: list[str]) -> str:
    """{linhaOrigem}:{sha256hex} do conteúdo da linha. Não gera UUID."""
    payload = "\u001f".join(celulas)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{linha_origem}:{digest}"


_COLUNAS_CONTATO = {
    "telefone": "telefone",
    "email": "email",
    "e-mail": "email",
    "busca lkd": "buscaLkd",
}


def colunas_contato(nomes: list[str]) -> dict[str, str]:
    """Ache Telefone, Email e Busca LKD pelo cabeçalho do mapa, sem o operador mapear de novo."""
    achadas: dict[str, str] = {}
    for nome in nomes:
        chave = " ".join(str(nome).strip().casefold().split())
        campo = _COLUNAS_CONTATO.get(chave)
        if campo and campo not in achadas:
            achadas[campo] = nome
    return achadas


def sugerir_ultimo_cargo(colunas: list[str]) -> str | None:
    """Sugere Cargo se existir. Não sugere Cargo Anterior (ADR 006)."""
    for col in colunas:
        if col.strip() == "Cargo":
            return col
    return None


def sugerir_empresa(colunas: list[str]) -> str | None:
    """Sugere Empresa se existir e o operador ainda não escolheu outra."""
    for col in colunas:
        if str(col).strip() == "Empresa":
            return col
    return None


def nome_cabecalho(col: object) -> str:
    texto = "" if col is None else str(col).strip()
    if _UNNAMED.fullmatch(texto):
        return ""
    return texto


def ajustar_cabecalhos(df: pd.DataFrame) -> pd.DataFrame:
    ajustado = df.copy()
    ajustado.columns = [nome_cabecalho(col) for col in df.columns]
    return ajustado


def _celula_texto(valor: object) -> str:
    if valor is None:
        return ""
    texto = str(valor)
    if texto.lower() == "nan":
        return ""
    return texto


def _linha_vazia(celulas: list[str]) -> bool:
    return all(c.strip() == "" for c in celulas)


def _dataframe_de_bytes(conteudo: bytes, nome_arquivo: str, encoding: str) -> pd.DataFrame:
    nome = (nome_arquivo or "").lower()
    if nome.endswith(".xlsx") or nome.endswith(".xlsm"):
        return pd.read_excel(
            io.BytesIO(conteudo), engine="openpyxl", dtype=str, keep_default_na=False, index_col=None
        )
    if encoding == "utf-8":
        try:
            texto = conteudo.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ErroImportacao(MSG_UTF8_INVALIDO) from exc
    elif encoding == "latin-1":
        texto = conteudo.decode("latin-1")
    else:
        try:
            texto = conteudo.decode(encoding)
        except LookupError as exc:
            raise ErroImportacao(f"Encoding não suportado: {encoding}.") from exc
        except UnicodeDecodeError as exc:
            raise ErroImportacao(MSG_UTF8_INVALIDO) from exc
    return pd.read_csv(io.StringIO(texto), dtype=str, keep_default_na=False, index_col=False)


def previsualizar(conteudo: bytes, nome_arquivo: str, encoding: str) -> dict[str, Any]:
    if not conteudo:
        raise ErroImportacao(MSG_ARQUIVO_AUSENTE)
    df = ajustar_cabecalhos(_dataframe_de_bytes(conteudo, nome_arquivo, encoding))
    colunas = [str(c) for c in df.columns.tolist()]
    linhas: list[dict[str, str]] = []
    for _, row in df.head(5).iterrows():
        linhas.append({col: _celula_texto(row.get(col, "")) for col in colunas})
    return {
        "colunas": colunas,
        "linhas": linhas,
        "sugestaoUltimoCargo": sugerir_ultimo_cargo(colunas),
        "sugestaoEmpresa": sugerir_empresa(colunas),
        "encoding": encoding,
        "xlsx": nome_arquivo.lower().endswith((".xlsx", ".xlsm")),
    }


def _valor_coluna(row: pd.Series, coluna: str | None) -> str | None:
    if not coluna:
        return None
    if coluna not in row.index:
        return None
    texto = _celula_texto(row[coluna])
    return texto


def confirmar_lote(
    conteudo: bytes,
    nome_arquivo: str,
    encoding: str,
    mapeamento: dict[str, Any],
    projeto_id: str,
) -> list[dict[str, Any]]:
    if not conteudo:
        raise ErroImportacao(MSG_ARQUIVO_AUSENTE)
    df = ajustar_cabecalhos(_dataframe_de_bytes(conteudo, nome_arquivo, encoding))
    df = df.reset_index(drop=True)
    colunas = [str(c) for c in df.columns.tolist()]
    for col_resp in mapeamento.get("respostasChatbot") or []:
        if nome_cabecalho(col_resp) == "":
            raise ErroImportacao(MSG_COLUNA_RESPOSTA_SEM_NOME)
    contato = colunas_contato(colunas)
    candidatos: list[dict[str, Any]] = []
    for indice, row in df.iterrows():
        linha_origem = int(indice) + 1
        celulas = [_celula_texto(row.get(col, "")) for col in colunas]
        if _linha_vazia(celulas):
            continue
        respostas: list[dict[str, str]] = []
        for col_resp in mapeamento.get("respostasChatbot") or []:
            nome = nome_cabecalho(col_resp)
            if not nome:
                continue
            respostas.append({"colunaMapeada": nome, "texto": _celula_texto(row.get(nome, ""))})
        candidatos.append(
            {
                "candidatoId": gerar_candidato_id(linha_origem, celulas),
                "projetoId": projeto_id,
                "linhaOrigem": linha_origem,
                "ultimoCargo": _valor_coluna(row, mapeamento.get("ultimoCargo")),
                "idade": _valor_coluna(row, mapeamento.get("idade")),
                "escolaridade": _valor_coluna(row, mapeamento.get("escolaridade")),
                "empresa": _valor_coluna(row, mapeamento.get("empresa")),
                "nomeExibicao": _valor_coluna(row, mapeamento.get("nomeExibicao")),
                "telefone": _valor_coluna(row, contato.get("telefone")),
                "email": _valor_coluna(row, contato.get("email")),
                "buscaLkd": _valor_coluna(row, contato.get("buscaLkd")),
                "cidade": _valor_coluna(row, mapeamento.get("cidade")),
                "statusLegado": _valor_coluna(row, mapeamento.get("statusLegado")),
                "respostasChatbot": respostas,
            }
        )
    if not candidatos:
        raise ErroImportacao(MSG_SEM_CANDIDATOS)
    return candidatos
