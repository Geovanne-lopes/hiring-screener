from __future__ import annotations

from texto_util import normalizar

from avaliacao_ia.resposta import respostas_utilizaveis

INSTRUCOES_TECNICAS = """INSTRUÇÕES TÉCNICAS DE FORMATO
Responda somente com um único objeto JSON válido.
Não use markdown, não use cerca de código, não escreva texto antes ou depois do JSON.
O objeto tem exatamente as chaves: perfil, compatibilidade, por_criterio, trechos.
por_criterio é uma lista com um item para cada critério qualitativo informado, na mesma ordem, cada um com: criterioId, nome, resultado, justificativa.
resultado é exatamente um de: atende, atende_parcialmente, nao_atende, sem_informacao.
trechos é uma lista na mesma ordem de por_criterio, cada item com: criterioId, nome, trecho.
Se resultado for sem_informacao, trecho é string vazia.
Não invente chaves extras."""

TEMPLATE_INICIAL = """Você avalia respostas de chatbot de uma pessoa que já passou na triagem determinística desta vaga.
Não julgue cargo, idade nem escolaridade.
Não decida se a pessoa entra ou sai do processo por esses atributos.
Não invente experiência, disponibilidade, habilidade, empregador, período ou qualquer fato que não esteja nas respostas delimitadas abaixo.
Não escreva cadeia de raciocínio.
Não escreva texto fora do JSON.

## Critérios qualitativos da vaga
{{criterios_qualitativos}}

## Identificador
{{candidato_id}}

## Respostas do chatbot
{{respostas_candidato}}

## Tarefa
1. Em "perfil", escreva um parágrafo curto (no máximo cinco frases) traçando o perfil somente a partir das respostas.
2. Em "por_criterio", julgue cada critério qualitativo listado. Use "sem_informacao" quando as respostas não permitirem julgar — nunca use "atende" nesse caso.
3. Em "justificativa", cite o trecho literal quando houver resposta correspondente.
4. Em "trechos", copie o trecho literal da resposta que sustentou o julgamento; deixe vazio se o resultado for "sem_informacao".
5. Preencha "compatibilidade" com exatamente um de: compativel, parcial, incompativel. O sistema recalcula esse campo pela regra da operação; preencha mesmo assim de forma coerente com os julgamentos.

Saída: somente o objeto JSON."""

MSG_PROMPT_JULGA_DURA = (
    "O prompt não pode pedir ao modelo que julgue cargo, idade ou escolaridade. Isso já foi decidido na triagem."
)

MSG_CRITERIOS_DESALINHADOS = (
    "Os critérios qualitativos mudaram desde a última versão salva do prompt. "
    "Salve o prompt para gerar uma versão com os critérios atuais antes de avaliar."
)

TERMOS_REGRA_DURA = (
    "idade",
    "faixa etaria",
    "escolaridade",
    "ultimo cargo",
    "cargos aceitos",
)


def formatar_criterios(itens: list[dict]) -> str:
    linhas: list[str] = []
    ordenados = sorted(itens, key=lambda x: int(x.get("ordem") or 0))
    for item in ordenados:
        elim = "sim" if item.get("eliminatorio") else "não"
        ordem = item.get("ordem")
        linhas.append(
            f"{ordem}. {item.get('nome')} (eliminatório: {elim})\n"
            f"   criterioId: {item.get('criterioId')}\n"
            f"   {item.get('descricao')}"
        )
    return "\n".join(linhas)


def formatar_respostas(respostas: list[dict]) -> str:
    blocos = []
    for item in respostas_utilizaveis(respostas):
        blocos.append(
            f"[coluna mapeada pelo operador: {item['colunaMapeada']}]\n{item['texto']}"
        )
    return "\n\n".join(blocos)


def interpolar(template: str, candidato_id: str, itens: list[dict], respostas: list[dict]) -> str:
    return (
        template.replace("{{candidato_id}}", candidato_id)
        .replace("{{criterios_qualitativos}}", formatar_criterios(itens))
        .replace("{{respostas_candidato}}", formatar_respostas(respostas))
    )


def texto_preview(template: str, candidato_id: str, itens: list[dict], respostas: list[dict]) -> str:
    return INSTRUCOES_TECNICAS + "\n\n" + interpolar(template, candidato_id, itens, respostas)


def validar_template(template: str) -> str | None:
    n = normalizar(template)
    if "{{idade}}" in n or "{{cargo}}" in n or "{{escolaridade}}" in n:
        return MSG_PROMPT_JULGA_DURA
    if "julgue a idade" in n or "julgue o cargo" in n or "julgue a escolaridade" in n:
        return MSG_PROMPT_JULGA_DURA
    if "julgue a idade/o cargo/a escolaridade do candidato" in n:
        return MSG_PROMPT_JULGA_DURA
    return None


def parece_regra_dura(nome: str, descricao: str) -> bool:
    texto = normalizar(f"{nome} {descricao}")
    return any(termo in texto for termo in TERMOS_REGRA_DURA)
