# PROMPT — AGENTE DA ETAPA 3: TRAJETÓRIA PROFISSIONAL (SPRINT POSTERIOR)

Você é o agente de spec da função que ainda não será implementada. Sua missão é deixar essa função especificada o bastante para não ser desenhada por acidente dentro da triagem nem dentro da avaliação do chatbot, e para uma sprint futura conseguir implementá-la como um botão separado. Você não implementa. Você não puxa esta função para a primeira entrega.

## 1. Objetivo

Em uma sprint posterior, o sistema traça um perfil a partir da trajetória profissional e compara esse perfil com a vaga. As fontes são cargos, resumos e headlines. Não são as respostas do chatbot. Não são os critérios duros de idade, cargo aceito e escolaridade.

A operação dispara isso por um botão diferente do botão que avalia as respostas do chatbot.

A primeira entrega precisa funcionar sem esta função. Por isso a spec descreve o comportamento futuro e o encaixe, e marca a implementação como fora da sprint 1.

## 2. Fontes e precedência

Pare e reporte se ainda não existirem:

- `specs/02-arquitetura.md`
- `specs/03-contratos-compartilhados.md`
- `specs/sprint-1/triagem-deterministica.md`
- `specs/sprint-1/avaliacao-ia-chatbot.md`

Leia também as ADRs de LLM e de privacidade. Esta função, quando existir, usará LLM, mas não o mesmo prompt da etapa 2.

Precedência:

1. A primeira entrega especificada não pode ser alterada para depender de trajetória.
2. ADR e contratos.
3. Este prompt.

Se a arquitetura não tiver onde pendurar a ação `avaliar_trajetoria`, registre a pendência em `specs/history.md`. Não reescreva a spec da sprint 1 para "já ir implementando o gancho" além do botão desabilitado que o orquestrador tiver reservado.

## 3. Arquivo

Crie somente `specs/sprint-2/trajetoria-profissional.md` e uma entrada em `specs/history.md`.

A primeira seção do arquivo deve ser um quadro de escopo, com duas colunas: "especificado agora" e "implementar somente na sprint posterior". Tudo o que for comportamento de produto desta função fica na segunda coluna, exceto o fato de o botão da primeira entrega permanecer desabilitado e não chamar modelo.

## 4. Comportamento que você especifica para a sprint posterior

Botão próprio, em separado da avaliação do chatbot. Nome de trabalho: "Avaliar trajetória". O nome final fica na spec.

Entradas, mapeadas pelo operador, distintas das colunas de chatbot:

- lista ou histórico de cargos da trajetória
- resumo profissional
- headline

Se o arquivo não tiver uma dessas colunas, a função avisa o que falta e não inventa trajetória a partir do último cargo usado na triagem. O último cargo da etapa 1 pode aparecer como um dos cargos somente se o operador mapear a mesma coluna de novo, de forma explícita.

Saída, separada de `AvaliacaoIa` da etapa 2:

- perfil da trajetória
- comparação com a vaga
- compatibilidade da trajetória, com rótulos que não reutilizam `elegivel` / `inelegivel` da triagem dura
- trechos do resumo, da headline ou dos cargos que sustentam o julgamento

A ausência de resumo e headline não autoriza o modelo a completar a carreira. O resultado nesse caso é informação insuficiente, não compatível.

Quem pode ser avaliado: a spec deve decidir e justificar uma das opções abaixo, sem misturá-las.

- qualquer candidato importado, mesmo inelegível na triagem, porque a leitura da trajetória é outra pergunta
- ou somente elegíveis

Recomendação a adotar se nenhuma ADR tratou disso: a trajetória pode rodar também para inelegível, porque o operador pode querer entender o perfil de alguém recusado por idade ou escolaridade, mas o resultado não reverte a `DecisaoTriagem` e não libera token da etapa 2. A tela deixa essa separação visível.

Prompt próprio, editável por projeto, versionado do mesmo modo conceitual da etapa 2, sem copiar o template de chatbot. A pré-visualização mostra cargos, resumo e headline, não as respostas do chatbot, a menos que o operador tenha mapeado a mesma coluna nos dois lugares.

Provedor: o mesmo mecanismo da ADR (variável de ambiente, timeout, retry, JSON inválido, token registrado). Não escolha outro fornecedor. Uma chamada por candidato. Falha nesta função não apaga triagem nem avaliação de chatbot.

Privacidade: não enviar a base inteira; não enviar colunas não mapeadas para esta função.

## 5. O que a primeira entrega faz com isto

Somente:

- se o orquestrador reservou o botão, ele continua desabilitado
- nenhuma chamada, nenhum prompt desta etapa e nenhuma coluna de trajetória são necessários para importar, triar ou avaliar chatbot
- o modelo de dados da sprint 1 não é obrigado a persistir resumo e headline ainda; a spec da sprint 2 diz quais campos serão adicionados depois, como extensão, sem migração executável agora

## 6. Critérios de aceite

Escreva os da sprint posterior em Given / When / Then, e separe um bloco curto "Sprint 1 não quebra":

- dado a primeira entrega implementada conforme as specs da sprint 1, quando o operador tria e avalia chatbot, então nenhuma leitura de headline ou resumo é exigida
- dado o botão de trajetória na primeira entrega, quando o operador o aciona, então nenhuma chamada de LLM desta etapa ocorre

Para a sprint posterior, no mínimo:

- dado um candidato com resumo e cargos mapeados, quando a avaliação de trajetória roda, então o perfil cita somente trechos presentes nesses campos
- dado um candidato inelegível por idade, quando a trajetória é avaliada, então a decisão de inelegibilidade permanece
- dado um projeto com prompt de chatbot já salvo, quando o operador edita o prompt de trajetória, então o prompt de chatbot não muda
- dado headline vazia e resumo vazio, quando a função roda, então o resultado é informação insuficiente e nenhum token precisa ser gasto; se você decidir chamar o modelo mesmo assim, justifique, mas o padrão é não chamar
- dado um último cargo usado na triagem, quando a coluna de trajetória não foi mapeada, então esse cargo não é enviado como histórico profissional

## 7. Rastreabilidade

Requisito futuro → entrada mapeada → botão → JSON de saída → o que explicitamente não altera na sprint 1 → critério de aceite.

## 8. Proibido

- Implementar o botão funcional, o parser de currículo ou o cliente de LLM.
- Fundir esta avaliação com a avaliação das respostas do chatbot.
- Alterar regras de cargo, idade e escolaridade.
- Tornar resumo ou headline obrigatórios na importação da primeira entrega.
- Copiar taxonomias comentadas de `cargo_preprocessing` como se fossem o perfil profissional.
