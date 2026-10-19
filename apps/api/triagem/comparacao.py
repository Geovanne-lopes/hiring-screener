"""Comparação local de cargo e empresa, e leitura de idade. Sem HTTP e sem modelo."""

from __future__ import annotations

import re

from triagem.normalizacao import normalizar, texto_apos_strip_e_espaco

SEPARADORES = ("/", "|", "-", "–", "—", ",", ";")

_PARA_ABREV = {
    "senior": "sr",
    "pleno": "pl",
    "plena": "pl",
    "junior": "jr",
}
_DA_ABREV = {
    "sr": ("senior",),
    "pl": ("pleno", "plena"),
    "jr": ("junior",),
}
_ALIAS = {
    "senior": ["Sênior", "Senior", "Sr", "Sr."],
    "sr": ["Sênior", "Senior", "Sr", "Sr."],
    "pleno": ["Pleno", "Plena", "Pl", "Pl."],
    "plena": ["Pleno", "Plena", "Pl", "Pl."],
    "pl": ["Pleno", "Plena", "Pl", "Pl."],
    "junior": ["Júnior", "Junior", "Jr", "Jr."],
    "jr": ["Júnior", "Junior", "Jr", "Jr."],
}
_ANO = {"ano", "anos", "year", "years"}
_MES = {"mes", "meses", "month", "months"}
_PURO = re.compile(r"^(\d+)(?:[.,](\d+))?$")


def palavras(texto: object) -> list[str]:
    """Normaliza, troca pontuação por espaço e devolve palavras inteiras."""
    base = normalizar(texto)
    for separador in SEPARADORES:
        base = base.replace(separador, " ")
    saida: list[str] = []
    for parte in base.split():
        token = parte.strip(".")
        if token:
            saida.append(token)
    return saida


def texto_comparado(texto: object) -> str:
    return " ".join(palavras(texto))


def variante_genero(token: str) -> str | None:
    """o↔a com miolo de 4+, ou or↔ora com miolo de 4+. Não vira gerente."""
    if len(token) >= 7 and token.endswith("ora"):
        miolo = token[:-3]
        if len(miolo) >= 4:
            return miolo + "or"
    if len(token) >= 6 and token.endswith("or"):
        miolo = token[:-2]
        if len(miolo) >= 4:
            return miolo + "ora"
    if len(token) >= 5 and token[-1] in ("o", "a"):
        miolo = token[:-1]
        if len(miolo) >= 4:
            return miolo + ("a" if token[-1] == "o" else "o")
    return None


def _abreviaturas(token: str) -> set[str]:
    extra: set[str] = set()
    if token in _PARA_ABREV:
        extra.add(_PARA_ABREV[token])
    if token in _DA_ABREV:
        extra.update(_DA_ABREV[token])
    return extra


def equivalentes(token: str, *, genero: bool, abreviacao: bool) -> set[str]:
    formas = {token}
    if genero:
        outra = variante_genero(token)
        if outra:
            formas.add(outra)
    if abreviacao:
        extra: set[str] = set()
        for forma in formas:
            extra |= _abreviaturas(forma)
        formas |= extra
        if genero:
            mais: set[str] = set()
            for forma in formas:
                outra = variante_genero(forma)
                if outra:
                    mais.add(outra)
            formas |= mais
            extra = set()
            for forma in formas:
                extra |= _abreviaturas(forma)
            formas |= extra
    return formas


def token_casa(esquerda: str, direita: str, *, genero: bool, abreviacao: bool) -> bool:
    return bool(
        equivalentes(esquerda, genero=genero, abreviacao=abreviacao)
        & equivalentes(direita, genero=genero, abreviacao=abreviacao)
    )


def frase_casa(celula: object, frase: object, *, genero: bool, abreviacao: bool) -> bool:
    """A frase casa se as palavras dela aparecem seguidas e na mesma ordem."""
    da_celula = palavras(celula)
    da_frase = palavras(frase)
    tamanho = len(da_frase)
    if tamanho == 0 or tamanho > len(da_celula):
        return False
    for inicio in range(len(da_celula) - tamanho + 1):
        if all(
            token_casa(da_celula[inicio + indice], da_frase[indice], genero=genero, abreviacao=abreviacao)
            for indice in range(tamanho)
        ):
            return True
    return False


def _partir_original(texto: str) -> list[str]:
    base = texto_apos_strip_e_espaco(texto)
    for separador in SEPARADORES:
        base = base.replace(separador, " ")
    saida: list[str] = []
    for parte in base.split():
        token = parte.strip(".")
        if token:
            saida.append(token)
    return saida


def _visivel(forma: str, digitada: str) -> bool:
    sem_ponto = digitada.strip(".")
    return forma.casefold() not in {digitada.casefold(), sem_ponto.casefold()}


def _genero_no_original(palavra: str, chave: str, outra: str) -> str | None:
    if chave.endswith("ora") and outra.endswith("or") and palavra.casefold().endswith("ora"):
        return palavra[:-3] + "or"
    if chave.endswith("or") and outra.endswith("ora") and palavra.casefold().endswith("or"):
        return palavra + "a"
    if chave.endswith("o") and outra.endswith("a") and palavra.casefold().endswith("o"):
        return palavra[:-1] + "a"
    if chave.endswith("a") and outra.endswith("o") and palavra.casefold().endswith("a"):
        return palavra[:-1] + "o"
    return None


def variantes_da_palavra(palavra: str) -> list[str]:
    chave = normalizar(palavra).strip(".")
    digitada = palavra.strip()
    if chave in _ALIAS:
        return [forma for forma in _ALIAS[chave] if _visivel(forma, digitada)]
    outra = variante_genero(chave)
    if not outra:
        return []
    exibicao = _genero_no_original(digitada.strip("."), chave, outra)
    if exibicao and _visivel(exibicao, digitada):
        return [exibicao]
    return []


def formas_que_tambem_entram(texto: object) -> list[str]:
    """Formas de gênero e das abreviações Sr, Pl e Jr. Sem tradução."""
    origem = _partir_original(str(texto or ""))
    if not origem:
        return []
    formas: list[str] = []
    vistas: set[str] = set()
    for indice, palavra in enumerate(origem):
        for variante in variantes_da_palavra(palavra):
            copia = list(origem)
            copia[indice] = variante
            frase = " ".join(copia)
            chave = frase.casefold()
            if chave in vistas or chave == texto_apos_strip_e_espaco(texto).casefold():
                continue
            vistas.add(chave)
            formas.append(frase)
    return formas


def _na_faixa(numero: int) -> int | None:
    if 1 <= numero <= 120:
        return numero
    return None


def parse_idade(valor: object) -> int | None:
    """Inteiro puro, ou inteiro com unidade de ano. Meses não somam. Sem chute."""
    texto = texto_apos_strip_e_espaco(valor)
    if not texto or normalizar(valor) == "#name?":
        return None
    puro = _PURO.fullmatch(texto)
    if puro:
        fracao = puro.group(2)
        if fracao is not None and int(fracao) != 0:
            return None
        return _na_faixa(int(puro.group(1)))
    bruto = normalizar(texto)
    for separador in ("-", "–", "—", "+", "/", "|"):
        bruto = bruto.replace(separador, " ")
    bruto = re.sub(r"(\d)([a-z])", r"\1 \2", bruto)
    bruto = re.sub(r"([a-z])(\d)", r"\1 \2", bruto)
    tokens = bruto.split()
    if len(tokens) == 2 and tokens[0].isdigit() and tokens[1] in _ANO:
        return _na_faixa(int(tokens[0]))
    if (
        len(tokens) == 4
        and tokens[0].isdigit()
        and tokens[1] in _ANO
        and tokens[2].isdigit()
        and tokens[3] in _MES
    ):
        return _na_faixa(int(tokens[0]))
    if (
        len(tokens) == 5
        and tokens[0].isdigit()
        and tokens[1] in _ANO
        and tokens[2] == "e"
        and tokens[3].isdigit()
        and tokens[4] in _MES
    ):
        return _na_faixa(int(tokens[0]))
    return None
