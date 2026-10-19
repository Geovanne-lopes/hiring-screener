"""Avaliação pura de um candidato contra critérios determinísticos. Zero HTTP."""

from __future__ import annotations

from typing import Any

from triagem.comparacao import frase_casa, palavras, parse_idade, texto_comparado
from triagem.normalizacao import normalizar, para_string, texto_apos_strip_e_espaco

CRITERIO_CARGO = "cargo"
CRITERIO_EMPRESA = "empresa"
CRITERIO_IDADE = "idade"
CRITERIO_ESCOLARIDADE = "escolaridade"

COD_CARGO_FORA = "cargo_fora_da_lista"
COD_CARGO_BLOQUEADO = "cargo_bloqueado"
COD_EMPRESA_BLOQUEADA = "empresa_bloqueada"
COD_IDADE_FORA = "idade_fora_da_faixa"
COD_ESC_FORA = "escolaridade_fora_da_lista"
COD_DADO_INVALIDO = "dado_obrigatorio_ausente_ou_invalido"

MSG_CARGOS_VAZIO = (
    "Não é possível executar a triagem: o critério de cargos está ativo e as listas de aceitos e de bloqueados estão vazias."
)
MSG_EMPRESAS_VAZIO = (
    "Não é possível executar a triagem: o critério de empresas bloqueadas está ativo e a lista está vazia."
)
MSG_IDADE_FAIXA = (
    "Não é possível executar a triagem: o critério de idade está ativo e a faixa (mínima e máxima) não está preenchida."
)
MSG_ESCOLARIDADE_VAZIA = (
    "Não é possível executar a triagem: o critério de escolaridade está ativo e a lista de valores aceitos está vazia."
)
MSG_IDADE_INVERTIDA = "Não é possível executar a triagem: a idade mínima é maior que a máxima."
MSG_SEM_LOTE = "Importe uma planilha antes de executar a triagem."
MSG_SEM_PROJETO = "Abra ou crie um projeto para continuar."


def criterios_iniciais() -> dict[str, Any]:
    return {
        "cargos": {"ativo": False, "aceitos": [], "bloqueados": []},
        "empresas": {"ativo": False, "bloqueadas": []},
        "idade": {"ativo": False, "minima": None, "maxima": None},
        "escolaridade": {
            "ativo": False,
            "configuracao": {"modelo": "lista_valores_aceitos", "aceitos": []},
        },
    }


def completar_criterios(criterios: dict[str, Any] | None) -> dict[str, Any]:
    """Critério antigo sem bloqueados ou sem empresas continua legível."""
    base = criterios_iniciais()
    if not criterios:
        return base
    cargos = criterios.get("cargos") or {}
    empresas = criterios.get("empresas") or {}
    idade = criterios.get("idade") or {}
    escolaridade = criterios.get("escolaridade") or {}
    configuracao = escolaridade.get("configuracao") or {}
    return {
        "cargos": {
            "ativo": bool(cargos.get("ativo")),
            "aceitos": list(cargos.get("aceitos") or []),
            "bloqueados": list(cargos.get("bloqueados") or []),
        },
        "empresas": {
            "ativo": bool(empresas.get("ativo")) if "empresas" in criterios else False,
            "bloqueadas": list(empresas.get("bloqueadas") or []),
        },
        "idade": {
            "ativo": bool(idade.get("ativo")),
            "minima": idade.get("minima", base["idade"]["minima"]),
            "maxima": idade.get("maxima", base["idade"]["maxima"]),
        },
        "escolaridade": {
            "ativo": bool(escolaridade.get("ativo")),
            "configuracao": {
                "modelo": configuracao.get("modelo") or "lista_valores_aceitos",
                "aceitos": list(configuracao.get("aceitos") or []),
            },
        },
    }


def incluir_item_lista(existentes: list[str], novo: object) -> tuple[list[str], str | None]:
    if texto_apos_strip_e_espaco(novo) == "":
        return list(existentes), "Item vazio ignorado."
    comparado_novo = normalizar(novo)
    for item in existentes:
        if normalizar(item) == comparado_novo:
            return list(existentes), "Este valor já está na lista."
    return [*existentes, para_string(novo).strip()], None


def _itens_validos(lista: list | None) -> list[str]:
    saida: list[str] = []
    for item in lista or []:
        atualizados, aviso = incluir_item_lista(saida, item)
        if aviso is None:
            saida = atualizados
    return saida


def _idade_int(valor: object) -> int | None:
    if valor is None or valor == "":
        return None
    try:
        n = int(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return n


def mensagens_bloqueio_execucao(
    criterios: dict[str, Any] | None,
    mapeamento: dict[str, Any] | None,
    quantidade_candidatos: int,
) -> list[str]:
    """Pré-condições do lote. Qualquer item bloqueia a execução inteira."""
    msgs: list[str] = []
    if criterios is None:
        return [MSG_SEM_PROJETO]
    if quantidade_candidatos < 1:
        msgs.append(MSG_SEM_LOTE)
        return msgs

    criterios = completar_criterios(criterios)
    cargos = criterios.get("cargos") or {}
    empresas = criterios.get("empresas") or {}
    idade = criterios.get("idade") or {}
    escolaridade = criterios.get("escolaridade") or {}
    mapa = mapeamento or {}

    if cargos.get("ativo"):
        aceitos = _itens_validos(cargos.get("aceitos"))
        bloqueados = _itens_validos(cargos.get("bloqueados"))
        if not aceitos and not bloqueados:
            msgs.append(MSG_CARGOS_VAZIO)
        if not (mapa.get("ultimoCargo") or "").strip():
            msgs.append(
                "Não é possível executar a triagem: o critério de cargo está ativo e a coluna correspondente não foi mapeada."
            )

    if empresas.get("ativo"):
        bloqueadas = _itens_validos(empresas.get("bloqueadas"))
        if not bloqueadas:
            msgs.append(MSG_EMPRESAS_VAZIO)
        if not (mapa.get("empresa") or "").strip():
            msgs.append(
                "Não é possível executar a triagem: o critério de empresa está ativo e a coluna correspondente não foi mapeada."
            )

    if idade.get("ativo"):
        minima = _idade_int(idade.get("minima"))
        maxima = _idade_int(idade.get("maxima"))
        if minima is None or maxima is None:
            msgs.append(MSG_IDADE_FAIXA)
        elif minima > maxima:
            msgs.append(MSG_IDADE_INVERTIDA)
        else:
            if not (1 <= minima <= 120 and 1 <= maxima <= 120):
                msgs.append(MSG_IDADE_FAIXA)
        if not (mapa.get("idade") or "").strip():
            msgs.append(
                "Não é possível executar a triagem: o critério de idade está ativo e a coluna correspondente não foi mapeada."
            )

    if escolaridade.get("ativo"):
        aceitos_esc = _itens_validos((escolaridade.get("configuracao") or {}).get("aceitos"))
        if not aceitos_esc:
            msgs.append(MSG_ESCOLARIDADE_VAZIA)
        if not (mapa.get("escolaridade") or "").strip():
            msgs.append(
                "Não é possível executar a triagem: o critério de escolaridade está ativo e a coluna correspondente não foi mapeada."
            )

    return msgs


def _parse_idade_celula(valor: object) -> int | None:
    return parse_idade(valor)


def _eh_lixo_formula(valor: object) -> bool:
    return normalizar(valor) == "#name?"


def _motivo(
    criterio: str,
    codigo: str,
    mensagem: str,
    valor_lido: object,
    valor_comparado: object | None,
    esperado: object | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "criterio": criterio,
        "codigo": codigo,
        "valorLido": None if valor_lido is None else para_string(valor_lido),
        "valorComparado": valor_comparado,
        "mensagem": mensagem,
    }
    if esperado is not None:
        item["esperado"] = esperado
    return item


def _celula_vazia(valor: object) -> bool:
    if valor is None or not isinstance(valor, str):
        return True
    return texto_apos_strip_e_espaco(valor) == ""


def _avaliar_cargo(candidato: dict[str, Any], criterios: dict[str, Any]) -> list[dict[str, Any]]:
    cargos = criterios.get("cargos") or {}
    aceitos: list[str] = list(cargos.get("aceitos") or [])
    bloqueados: list[str] = list(cargos.get("bloqueados") or [])
    lido = candidato.get("ultimoCargo")
    if _celula_vazia(lido):
        return [
            _motivo(
                CRITERIO_CARGO,
                COD_DADO_INVALIDO,
                "Dado obrigatório ausente ou inválido no critério cargo: último cargo não informado ou vazio.",
                lido,
                None,
            )
        ]
    comparado = texto_comparado(lido)
    motivos: list[dict[str, Any]] = []
    aceitos_validos = [item for item in aceitos if palavras(item)]
    if aceitos_validos and not any(
        frase_casa(lido, termo, genero=True, abreviacao=True) for termo in aceitos_validos
    ):
        lista_txt = ", ".join(aceitos_validos)
        motivos.append(
            _motivo(
                CRITERIO_CARGO,
                COD_CARGO_FORA,
                (
                    f'Último cargo "{lido}" (comparado como "{comparado}") '
                    f"não está na lista de cargos aceitos: {lista_txt}."
                ),
                lido,
                comparado,
                aceitos_validos,
            )
        )
    for termo in bloqueados:
        if not palavras(termo):
            continue
        if frase_casa(lido, termo, genero=True, abreviacao=True):
            motivos.append(
                _motivo(
                    CRITERIO_CARGO,
                    COD_CARGO_BLOQUEADO,
                    (
                        f'Último cargo "{lido}" (comparado como "{comparado}") '
                        f'contém o cargo bloqueado "{termo}".'
                    ),
                    lido,
                    comparado,
                    termo,
                )
            )
            break
    return motivos


def _avaliar_empresa(candidato: dict[str, Any], criterios: dict[str, Any]) -> dict[str, Any] | None:
    bloqueadas: list[str] = list((criterios.get("empresas") or {}).get("bloqueadas") or [])
    lido = candidato.get("empresa")
    if _celula_vazia(lido):
        return _motivo(
            CRITERIO_EMPRESA,
            COD_DADO_INVALIDO,
            "Dado obrigatório ausente ou inválido no critério empresa: empresa não informada ou vazia.",
            lido,
            None,
        )
    comparado = texto_comparado(lido)
    for termo in bloqueadas:
        if not palavras(termo):
            continue
        if frase_casa(lido, termo, genero=False, abreviacao=False):
            return _motivo(
                CRITERIO_EMPRESA,
                COD_EMPRESA_BLOQUEADA,
                (
                    f'Empresa "{lido}" (comparada como "{comparado}") '
                    f'contém a empresa bloqueada "{termo}".'
                ),
                lido,
                comparado,
                termo,
            )
    return None


def _avaliar_idade(candidato: dict[str, Any], criterios: dict[str, Any]) -> dict[str, Any] | None:
    idade_cfg = criterios.get("idade") or {}
    minima = int(idade_cfg["minima"])
    maxima = int(idade_cfg["maxima"])
    lido = candidato.get("idade")
    parseada = _parse_idade_celula(lido)
    if parseada is None:
        mostrado = "" if lido is None else para_string(lido)
        return _motivo(
            CRITERIO_IDADE,
            COD_DADO_INVALIDO,
            f'Dado obrigatório ausente ou inválido no critério idade: valor lido "{mostrado}".',
            None if lido is None else lido,
            None,
        )
    if parseada < minima or parseada > maxima:
        return _motivo(
            CRITERIO_IDADE,
            COD_IDADE_FORA,
            f"Idade {parseada} está fora da faixa {minima} a {maxima} (limites inclusivos).",
            para_string(lido),
            str(parseada),
            {"minima": minima, "maxima": maxima},
        )
    return None


def _avaliar_escolaridade(candidato: dict[str, Any], criterios: dict[str, Any]) -> dict[str, Any] | None:
    aceitos: list[str] = list(
        ((criterios.get("escolaridade") or {}).get("configuracao") or {}).get("aceitos") or []
    )
    lido = candidato.get("escolaridade")
    texto = texto_apos_strip_e_espaco(lido) if lido is not None else ""
    if lido is None or texto == "" or _eh_lixo_formula(lido):
        return _motivo(
            CRITERIO_ESCOLARIDADE,
            COD_DADO_INVALIDO,
            "Dado obrigatório ausente ou inválido no critério escolaridade: célula vazia, ausente ou lixo de fórmula (#NAME?).",
            None if lido is None else lido,
            None,
        )
    comparado = texto_comparado(lido)
    aceitos_validos = [item for item in aceitos if palavras(item)]
    if not any(frase_casa(lido, termo, genero=False, abreviacao=False) for termo in aceitos_validos):
        lista_txt = ", ".join(aceitos_validos)
        return _motivo(
            CRITERIO_ESCOLARIDADE,
            COD_ESC_FORA,
            (
                f'Escolaridade "{lido}" (comparada como "{comparado}") '
                f"não contém nenhuma frase aceita: {lista_txt}."
            ),
            lido,
            comparado,
            aceitos_validos,
        )
    return None


def avaliar_candidato(candidato: dict[str, Any], criterios: dict[str, Any]) -> dict[str, Any]:
    """Função pura. Avalia todos os critérios ativos; não para na primeira falha."""
    criterios = completar_criterios(criterios)
    motivos: list[dict[str, Any]] = []
    inativos: list[str] = []

    cargos = criterios.get("cargos") or {}
    empresas = criterios.get("empresas") or {}
    idade = criterios.get("idade") or {}
    escolaridade = criterios.get("escolaridade") or {}

    if cargos.get("ativo"):
        motivos.extend(_avaliar_cargo(candidato, criterios))
    else:
        inativos.append(CRITERIO_CARGO)

    if empresas.get("ativo"):
        motivo = _avaliar_empresa(candidato, criterios)
        if motivo:
            motivos.append(motivo)
    else:
        inativos.append(CRITERIO_EMPRESA)

    if idade.get("ativo"):
        motivo = _avaliar_idade(candidato, criterios)
        if motivo:
            motivos.append(motivo)
    else:
        inativos.append(CRITERIO_IDADE)

    if escolaridade.get("ativo"):
        motivo = _avaliar_escolaridade(candidato, criterios)
        if motivo:
            motivos.append(motivo)
    else:
        inativos.append(CRITERIO_ESCOLARIDADE)

    return {
        "candidatoId": candidato.get("candidatoId"),
        "projetoId": candidato.get("projetoId"),
        "resultado": "inelegivel" if motivos else "elegivel",
        "motivos": motivos,
        "criteriosInativos": inativos,
    }
