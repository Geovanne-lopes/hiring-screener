from __future__ import annotations

from texto_util import normalizar

from avaliacao_ia.resposta import pares_da_linha

INSTRUCOES_TECNICAS = """INSTRUÇÕES TÉCNICAS DE FORMATO
Responda somente com um único objeto JSON válido.
Não use markdown, não use cerca de código, não escreva texto antes ou depois do JSON.
O objeto tem exatamente as chaves: perfil, por_pergunta, trechos, nota_tecnica, nota_comportamental, justificativa_nota_tecnica, justificativa_nota_comportamental.
por_pergunta é uma lista com um item para cada pergunta enviada, na mesma ordem, cada um com: perguntaId, pergunta, resultado, justificativa.
resultado é exatamente um de: atende, atende_parcialmente, nao_atende, sem_informacao.
trechos é uma lista na mesma ordem, cada item com: perguntaId, trecho.
Se resultado for sem_informacao, trecho é string vazia.
nota_tecnica e nota_comportamental são inteiros de 0 a 100.
justificativa_nota_tecnica é um parágrafo de no máximo três frases que explica por que o inteiro cabe na faixa da rubrica técnica.
justificativa_nota_comportamental é um parágrafo de no máximo três frases que explica por que o inteiro cabe na faixa da escrita.
Os dois parágrafos não se copiam. perfil continua sendo só o resumo e não explica a nota.
Não invente chaves extras.
O texto marcado como job description é a descrição geral da vaga. Use-o como contexto do que a vaga pede. Ele não reabre cargo, idade nem escolaridade."""

TEMPLATE_INICIAL = """Você avalia respostas de chatbot de uma pessoa que já passou na triagem determinística desta vaga.
A descrição geral da vaga está em job description. Ela explica o contexto da vaga. Não é uma lista de critérios à parte.
Cada bloco em perguntas e respostas traz a pergunta no cabeçalho da coluna e a resposta do candidato.
Julgue se a resposta faz sentido para aquela pergunta, lida junto com a job description.
Não julgue cargo, idade nem escolaridade.
Não invente experiência, ferramenta, empregador, período ou fato que não esteja na resposta.
Não trate um trecho da job description como se o candidato o tivesse escrito.
Não escreva cadeia de raciocínio.
Não escreva texto fora do JSON.

## Job description
{{job_description}}

## Identificador
{{candidato_id}}

## Perguntas e respostas
{{perguntas_respostas}}

## Tarefa
1. Em "perfil", escreva um parágrafo curto (no máximo cinco frases) só com o que as respostas sustentam à luz da job description.
2. Em "por_pergunta", um item por pergunta enviada, na mesma ordem. "sem_informacao" quando a resposta não permite julgar o sentido da pergunta. Nunca use "atende" nesse caso.
3. Em "justificativa", explique o cruzamento entre a resposta, a pergunta e a job description. O trecho citado tem de estar na resposta, não na job description.
4. Em "trechos", copie o trecho literal da resposta. Vazio se o resultado for "sem_informacao".
5. "nota_tecnica": inteiro de 0 a 100. Quanto a resposta, cruzada com a pergunta, se aproxima do que a job description pede. Escala na spec de rankings.
6. "nota_comportamental": inteiro de 0 a 100. Qualidade da escrita do candidato nas respostas enviadas. Escala na spec de rankings.
7. "justificativa_nota_tecnica": por que a nota técnica está naquela faixa.
8. "justificativa_nota_comportamental": por que a nota comportamental está naquela faixa.

Saída: somente o objeto JSON."""

PARAGRAFO_JUSTIFICATIVAS_NOTA = (
    "A lista de chaves das instruções técnicas prevalece. "
    "Inclua justificativa_nota_tecnica e justificativa_nota_comportamental. "
    "Cada uma é um parágrafo de no máximo três frases que explica o inteiro daquela nota. "
    "perfil continua sendo só o resumo."
)

MSG_PROMPT_JULGA_DURA = (
    "O prompt não pode pedir ao modelo que julgue cargo, idade ou escolaridade. Isso já foi decidido na triagem."
)

MSG_JOB_DESCRIPTION_DESALINHADA = (
    "A job description mudou desde a última versão salva do prompt. "
    "Salve o prompt para gerar uma versão com a descrição atual antes de avaliar."
)

MSG_DELIMITADORES = (
    "O prompt precisa das variáveis da job description, das perguntas e respostas e do identificador."
)

MSG_CRITERIOS_FORA = (
    "Critérios qualitativos não fazem mais parte da avaliação. "
    "A IA cruza cada pergunta (nome da coluna) com a resposta e com a job description."
)

MSG_PROMPT_SEM_JOB = "Salve a job description da vaga antes de salvar o prompt."

DELIMITADORES_OBRIGATORIOS = ("{{job_description}}", "{{perguntas_respostas}}", "{{candidato_id}}")

TERMOS_REGRA_DURA = (
    "idade",
    "faixa etaria",
    "escolaridade",
    "ultimo cargo",
    "cargos aceitos",
)


def formatar_perguntas_respostas(respostas: list[dict] | None) -> str:
    blocos = []
    for par in pares_da_linha(respostas):
        blocos.append(
            f"Pergunta {par['perguntaId']}\n"
            f"Cabeçalho: {par['pergunta']}\n"
            f"Resposta:\n"
            f"{par['texto']}"
        )
    return "\n\n".join(blocos)


def interpolar(
    template: str,
    candidato_id: str,
    respostas: list[dict],
    job_description: str = "",
) -> str:
    parcial = template.replace("{{candidato_id}}", candidato_id).replace(
        "{{perguntas_respostas}}", formatar_perguntas_respostas(respostas)
    )
    return parcial.replace("{{job_description}}", job_description)


def texto_usuario(
    template: str,
    candidato_id: str,
    respostas: list[dict],
    job_description: str = "",
) -> str:
    return interpolar(template, candidato_id, respostas, job_description) + "\n\n" + PARAGRAFO_JUSTIFICATIVAS_NOTA


def texto_preview(
    template: str,
    candidato_id: str,
    respostas: list[dict],
    job_description: str = "",
) -> str:
    return INSTRUCOES_TECNICAS + "\n\n" + texto_usuario(template, candidato_id, respostas, job_description)


def validar_template(template: str) -> str | None:
    n = normalizar(template)
    if "{{idade}}" in n or "{{cargo}}" in n or "{{escolaridade}}" in n:
        return MSG_PROMPT_JULGA_DURA
    if "julgue a idade" in n or "julgue o cargo" in n or "julgue a escolaridade" in n:
        return MSG_PROMPT_JULGA_DURA
    if "julgue a idade/o cargo/a escolaridade do candidato" in n:
        return MSG_PROMPT_JULGA_DURA
    if "{{criterios_qualitativos}}" in (template or ""):
        return MSG_CRITERIOS_FORA
    if any(delimitador not in (template or "") for delimitador in DELIMITADORES_OBRIGATORIOS):
        return MSG_DELIMITADORES
    return None


def template_e_antigo(template: str | None) -> bool:
    if not template or not template.strip():
        return False
    if "{{criterios_qualitativos}}" in template or "{{respostas_candidato}}" in template:
        return True
    return any(delimitador not in template for delimitador in DELIMITADORES_OBRIGATORIOS)


def parece_regra_dura(nome: str, descricao: str) -> bool:
    texto = normalizar(f"{nome} {descricao}")
    return any(termo in texto for termo in TERMOS_REGRA_DURA)
