# Revisão — Análise por pergunta da coluna

Spec que **substitui a etapa de critérios qualitativos** na avaliação por IA.

A base da análise passa a ser o cruzamento de três coisas, por candidato elegível:

1. a **pergunta**, que é o cabeçalho da coluna mapeada;
2. a **resposta**, que é o texto da célula dessa coluna;
3. a **job description** vigente embutida no prompt (`specs/revisao/01-job-description.md`).

Selecionar três colunas significa três pares pergunta/resposta. Não há lista de critérios qualitativos para cadastrar.

Esta spec **não** reescreve `specs/sprint-1/avaliacao-ia-chatbot.md`. Para disparo novo, prevalece este arquivo nas partes em conflito (`specs/history.md`). O gate de quem pode ir ao modelo **não** muda.

Notas e ranking: o JSON desta chamada já traz `nota_tecnica` e `nota_comportamental`. Escala, média e posições estão em `specs/revisao/03-rankings.md`. Uma HTTP por candidato. O modelo não devolve posição no lote.

---

## 1. Decisões fechadas

| Tema | Decisão |
|---|---|
| Critérios qualitativos | Deixam de ser etapa, de ser obrigatórios e de ser injetados. A tela some da navegação. O disparo **não** lê `CriteriosQualitativos` |
| Pergunta | Texto do cabeçalho da coluna, como está no arquivo depois de strip do nome. Ex.: `Como você identifica as necessidades do cliente e personaliza sua abordagem para o atendimento?` |
| Resposta | Célula dessa coluna na linha do candidato |
| Quantas colunas | Uma ou mais, as que o operador mapeou em `respostasChatbot[]`. Três colunas = três pares. Zero colunas mapeadas: a avaliação por IA não roda |
| O que a IA julga em cada par | Se a resposta faz sentido para **aquela pergunta**, lida à luz da job description. Não julga uma lista de critérios à parte |
| Veredito agregado antigo | `compativel` / `parcial` / `incompativel` e a flag `eliminatorio` **não** são calculados em disparo novo. O agregado desta revisão são as notas e os rankings da spec 03 |
| `sem_informacao` | Continua existindo no julgamento de cada pergunta. Nunca equivale a “a resposta atende” |
| Chamada | Uma HTTP por candidato selecionado. Pré-visualizar não chama |
| Payload mínimo | Job description da versão embutida no prompt, pares pergunta/resposta utilizáveis, `candidatoId`, template. Sem nome, idade, cargo, escolaridade, cidade, telefone, e-mail, busca LKD, status legado |
| Dados já gravados | Avaliações antigas permanecem com o schema antigo. Disparo novo grava o schema desta revisão. Reimportar o lote continua apagando avaliações daquele projeto |

Opção rejeitada: manter a tela de critérios qualitativos como “opcional por cima” das perguntas. A operação pediu que o cruzamento pergunta + resposta + job description seja a base, sem essa etapa.

---

## 2. Quem entra na chamada

Igual à etapa 2 já especificada. Não se reabre.

| Situação | Chama? |
|---|---|
| Inelegível na triagem | Não. O texto da resposta não viaja, mesmo com colunas mapeadas |
| Elegível sem resposta utilizável | Não. Estado `aguardando_resposta` |
| Elegível com resposta, desmarcado neste lote | Não |
| Elegível com resposta, marcado, job description e prompt alinhados | Sim |

Resposta utilizável: pelo menos um par mapeado cujo texto, depois de string, strip e colapso de whitespace, tem comprimento maior que zero.

Pares vazios **não** entram no prompt. Se os três cabeçalhos foram mapeados e só duas células têm texto, viajam duas perguntas. A pergunta da célula vazia não é julgada nessa pessoa.

---

## 3. Mapeamento: a coluna é a pergunta

A importação continua sendo o lugar em que o operador escolhe as colunas. Esta spec acrescenta texto fixo nessa escolha:

> O nome da coluna é a pergunta. A IA cruza a resposta do candidato com essa pergunta e com a job description. Não há critérios qualitativos separados.

Regras:

- A ordem em que as colunas foram confirmadas no mapeamento é a ordem dos pares.
- Cabeçalho vazio depois de strip não pode ser confirmado como coluna de resposta. Mensagem: “A coluna de resposta precisa de um nome, porque esse nome é a pergunta.”
- Não inventar o texto da pergunta. Não resumir o cabeçalho no código. Não transformar o cabeçalho em critério qualitativo por trás.
- Cargo, idade e escolaridade mapeados para a triagem **não** entram nesta lista, a menos que o operador mapeie de novo, de propósito, a mesma coluna também como resposta de chatbot. Nesse caso o texto viaja como resposta daquela pergunta, não como critério duro.

`perguntaId` de cada par: `p1`, `p2`, `p3`, … na ordem do mapeamento. O mesmo cabeçalho na mesma ordem produz o mesmo id em todas as linhas do lote.

---

## 4. O que sai do fluxo

- Rota e item de menu **Critérios qualitativos**.
- Obrigatoriedade de `criteriosQualitativos` e de `{{criterios_qualitativos}}` para disparar.
- Bloqueio “os critérios qualitativos mudaram desde o prompt”. No lugar entra o bloqueio da job description (`specs/revisao/01-job-description.md`).
- Regra de compatibilidade da secção 8 da spec antiga, nos disparos novos.
- Aviso de “não repita cargo/idade/escolaridade como critério qualitativo”: deixa de ter lista onde colar isso. O prompt continua proibido de pedir que o modelo julgue cargo, idade ou escolaridade.

Linhas antigas de `CriteriosQualitativos` podem ficar no banco. O disparo novo não as lê. Apagá-las não é requisito desta spec.

---

## 5. Prompt

O editor de prompt permanece. É o texto que a operação ajusta sem deploy. A job description e os pares **não** são digitados de novo no template: entram pelos delimitadores.

### 5.1 Delimitadores obrigatórios para salvar

| Delimitador | Conteúdo |
|---|---|
| `{{job_description}}` | snapshot da job description embutido na versão do prompt |
| `{{perguntas_respostas}}` | pares utilizáveis daquela pessoa, na ordem do mapeamento |
| `{{candidato_id}}` | `candidatoId` já persistido |

Salvar sem algum desses três recusa:

> O prompt precisa das variáveis da job description, das perguntas e respostas e do identificador.

Salvar com `{{criterios_qualitativos}}` recusa:

> Critérios qualitativos não fazem mais parte da avaliação. A IA cruza cada pergunta (nome da coluna) com a resposta e com a job description.

Proibições já existentes continuam: `{{idade}}`, `{{cargo}}`, `{{escolaridade}}`, pedido para julgar idade, cargo ou escolaridade, nome, cidade, equipe, status legado, cadeia de raciocínio oculta.

Cada save gera versão nova e copia `jobDescriptionVersaoId` + `jobDescriptionSnapshot`.

Se o template vigente ainda for o antigo, o editor mostra a versão salva e um aviso com ação **Usar o modelo desta revisão**. A ação preenche o editor com o texto da secção 5.3 e **não** salva sozinha.

### 5.2 Forma injetada de `{{perguntas_respostas}}`

Um bloco por par utilizável, separado por linha em branco:

```
Pergunta p1
Cabeçalho: Como você identifica as necessidades do cliente e personaliza sua abordagem para o atendimento?
Resposta:
(texto da célula, sem reescrever)
```

O rótulo `Cabeçalho:` deixa explícito que aquele texto é a pergunta da coluna, não um critério cadastrado à parte.

Não incluir telefone, e-mail, nome, busca LKD nem colunas não mapeadas como resposta.

### 5.3 Prefixo técnico (visível na pré-visualização)

Substitui o prefixo da spec antiga nos disparos novos. Cópia literal. Nada além disto no papel de formato:

```
INSTRUÇÕES TÉCNICAS DE FORMATO
Responda somente com um único objeto JSON válido.
Não use markdown, não use cerca de código, não escreva texto antes ou depois do JSON.
O objeto tem exatamente as chaves: perfil, por_pergunta, trechos, nota_tecnica, nota_comportamental.
por_pergunta é uma lista com um item para cada pergunta enviada, na mesma ordem, cada um com: perguntaId, pergunta, resultado, justificativa.
resultado é exatamente um de: atende, atende_parcialmente, nao_atende, sem_informacao.
trechos é uma lista na mesma ordem, cada item com: perguntaId, trecho.
Se resultado for sem_informacao, trecho é string vazia.
nota_tecnica e nota_comportamental são inteiros de 0 a 100.
Não invente chaves extras.
O texto marcado como job description é a descrição geral da vaga. Use-o como contexto do que a vaga pede. Ele não reabre cargo, idade nem escolaridade.
```

### 5.4 Template inicial

Gravar como próxima versão quando o operador usar o modelo desta revisão, e como primeira versão de prompt em projeto que ainda não tem prompt **depois** que existir job description salva. Sem job description salva, o primeiro save de prompt continua recusado pela spec 01.

```
Você avalia respostas de chatbot de uma pessoa que já passou na triagem determinística desta vaga.
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

Saída: somente o objeto JSON.
```

---

## 6. JSON de saída

Chaves exatas: `perfil`, `por_pergunta`, `trechos`, `nota_tecnica`, `nota_comportamental`.

`por_pergunta[]`:

| Campo | Regra |
|---|---|
| `perguntaId` | o mesmo `p1`, `p2`, … enviado |
| `pergunta` | igual ao cabeçalho enviado |
| `resultado` | `atende` \| `atende_parcialmente` \| `nao_atende` \| `sem_informacao` |
| `justificativa` | texto não vazio |

`trechos[]`: um item por pergunta, mesmo `perguntaId`, `trecho` literal contido na resposta daquela pergunta (comparação depois de colapsar whitespace). `sem_informacao` exige `trecho` vazio. Os outros três resultados exigem trecho não vazio e contido na resposta.

Falha de schema (lista com tamanho diferente do número de perguntas enviadas, id trocado, trecho inventado, nota ausente ou fora de 0–100, chave extra): uma tentativa de reparo de JSON, depois `falha_avaliacao`. Sem perfil inventado, sem nota persistida, sem ranking. `DecisaoTriagem` intacta.

Retry de rede continua só para rede, timeout e 5xx. JSON inválido não é retry de rede.

Exemplo mínimo com uma pergunta:

```json
{
  "perfil": "A resposta descreve escuta e ajuste de abordagem no atendimento, em linha com o que a vaga pede na job description.",
  "por_pergunta": [
    {
      "perguntaId": "p1",
      "pergunta": "Como você identifica as necessidades do cliente e personaliza sua abordagem para o atendimento?",
      "resultado": "atende",
      "justificativa": "A resposta conta como pergunta o contexto do cliente e muda a explicação. Isso conversa com a pergunta e com o atendimento descrito na job description."
    }
  ],
  "trechos": [
    {
      "perguntaId": "p1",
      "trecho": "eu pergunto o que a pessoa já tentou e explico de outro jeito"
    }
  ],
  "nota_tecnica": 78,
  "nota_comportamental": 70
}
```

---

## 7. Resultado por pergunta na tela

Na linha avaliada com sucesso, por pergunta enviada: cabeçalho, resultado, justificativa, trecho. Mais o perfil, a versão do prompt, a versão da job description e os tokens.

Não mostrar “compatível / parcial / incompatível” como veredito de disparo novo. Notas e posições: spec 03.

`sem_informacao` aparece como “sem informação para julgar esta pergunta”, nunca como pergunta atendida.

---

## 8. Critérios de aceite

### CA-P-01 — Três colunas, sem critérios qualitativos

Given três colunas mapeadas como resposta, job description vigente e prompt alinhado  
And a tela de critérios qualitativos não foi preenchida  
When o operador dispara a avaliação de um elegível com as três respostas preenchidas  
Then a chamada contém os três cabeçalhos como perguntas, as três respostas e a job description  
And não contém lista de critérios qualitativos

### CA-P-02 — Cabeçalho é a pergunta

Given a coluna `Como você identifica as necessidades do cliente e personaliza sua abordagem para o atendimento?`  
When o payload é montado  
Then esse texto aparece como pergunta `p1` (se for a primeira coluna mapeada)  
And a resposta é só a célula daquela linha

### CA-P-03 — Célula vazia não viaja

Given três colunas mapeadas e uma célula só com espaços  
When a chamada daquela linha é montada  
Then essa pergunta não entra  
And as outras duas entram

### CA-P-04 — Inelegível

Given inelegível com as colunas preenchidas  
When a avaliação é disparada  
Then não há chamada para essa pessoa

### CA-P-05 — Template antigo não salva

Given o editor com `{{criterios_qualitativos}}`  
When o operador salva  
Then a versão não é criada  
And a mensagem diz que critérios qualitativos não fazem mais parte da avaliação

### CA-P-06 — Trecho fora da resposta

Given JSON cuja justificativa cita a job description mas o `trecho` não está na célula  
When o backend valida  
Then o estado é `falha_avaliacao`  
And não há nota persistida  
And a decisão de triagem permanece

### CA-P-07 — sem_informacao não vira atendimento

Given `resultado = sem_informacao` com trecho vazio e schema válido no restante  
When a tela mostra a pergunta  
Then o rótulo é de informação insuficiente  
And não é mostrado como pergunta atendida

---

## 9. Fora desta spec

- Fórmula do ranking final e desempate (`specs/revisao/03-rankings.md`)
- Upload da job description (`specs/revisao/01-job-description.md`)
- Mudança de cargo, idade ou escolaridade
- Trajetória profissional
