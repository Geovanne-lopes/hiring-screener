# Sprint 1 — Avaliação por IA das respostas do chatbot

Spec da etapa 2. Permite a um agente implementador construir a avaliação qualitativa por LLM **depois** da triagem determinística, sem reabrir cargo, idade ou escolaridade.

Esta etapa **substitui a regressão logística do legado**. Não a evolui. Não usa `Status`, `contratado` nem `predict_proba` como rótulo. Não lê resumo, headline nem trajetória de cargos: isso é o agente 3.

O botão **Avaliar trajetória** permanece no lugar que o orquestrador reservou: visível, desabilitado, texto de sprint posterior, sem disparar modelo. Esta spec **não o habilita**.

Dono: agente 2 (`prompts/sdd/02-agente-avaliacao-ia-chatbot.md`).

Contratos: `CriteriosQualitativos`, `PromptDoProjeto`, `AvaliacaoIa` em `specs/03-contratos-compartilhados.md`. Quem pode ser enviado: `DecisaoTriagem` da etapa 1. Stack: módulo `avaliacao_ia` no backend, único ponto de rede para modelo (ADR 002, ADR 004). Payload mínimo: ADR 007.

---

## 1. Decisões fechadas nesta spec

| Tema | Decisão |
|---|---|
| Quem chama o LLM | Só `elegivel` na etapa 1 **e** com resposta de chatbot utilizável **e** incluído no lote desta execução |
| Disparo | Explícito. Abrir tela, pré-visualizar prompt ou listar candidatos **não** chama o provedor |
| Exclusão manual | Sim: a operação desmarca um elegível na lista do lote antes de gastar token. Não apaga `DecisaoTriagem` |
| Chamadas | Uma HTTP por candidato. A ADR 004 não definiu lote no provedor |
| Resposta utilizável | Pelo menos um item de `respostasChatbot[]` cujo texto, após trim e colapso de whitespace, não é vazio |
| Mapeamento | Sem coluna de chatbot mapeada no projeto, a etapa 2 **não roda**. Nomes de coluna **não são inventados** |
| Critério qualitativo | Nome + descrição do que conta como atendimento + ordem + flag `eliminatorio`. Não replica cargo/idade/escolaridade como porta de entrada |
| Versão | Salvar critérios gera `versaoId` novo. Salvar prompt gera versão nova (id, texto, data, critérios embutidos). Avaliação antiga não é reescrita |
| Compatibilidade | Calculada no backend pela regra da secção 8 a partir de `por_criterio`. Persistida a valor calculado, não um palpite solto do modelo |
| `sem_informacao` | Nunca vira `atende`. Na tela, nunca aparece como critério atendido |
| Reparo de JSON | Uma tentativa. Depois disso, `falha_avaliacao` |
| Retry de rede | Só falha de rede / timeout / 5xx, até `LLM_MAX_RETRIES`. JSON inválido não é retentado como rede |
| Trajetória | Fora. Sem endpoint ativo, sem leitura de headline/resumo/cargos para perfil de trajetória |
| Provedor | O da ADR 004 (`LLM_BASE_URL` + chave + modelo por ambiente). Esta spec não escolhe fornecedor |

### 1.1 O que o legado não faz (evidência, não requisito novo)

Confirmado em `data_vis_carrefour.py` e `model_ml.py` (repositório legado, não este):

- o funil conta `Enviado`, `Respondido` (`Status Chatbot == 'Respondido'`) e `Elegível`;
- o modelo treina `LogisticRegression` com one-hot de `Idade`, `Cargo` e `Escolaridade` e grava `Sim`/`Nao` via `predict_proba` e limiar 0,4;
- **não há leitura de texto de resposta de chatbot**.

Não há CSV/XLSX local neste disco. **Não há nome de coluna de resposta para congelar.** O operador indica, na importação já especificada pela etapa 1, quais colunas são perguntas/respostas do chatbot. Sem esse mapeamento, a avaliação por IA não roda.

`Status`, `Status Chatbot` e `Elegível` do legado **não** substituem o texto. Não são rótulo desta etapa.

---

## 2. Quem entra na chamada

Quatro estados de composição. Os três primeiros **não gastam token**.

| Estado de tela (`resultadoExibicao`) | Condição | Chama LLM? |
|---|---|---|
| `inelegivel` | `DecisaoTriagem.resultado = inelegivel` | Não. A tela mostra os `motivos` da etapa 1 |
| `aguardando_resposta` | `elegivel` e **sem** resposta utilizável (sem mapeamento, lista vazia, ou só textos vazios/whitespace) | Não |
| `elegivel_pendente_ia` | `elegivel` com resposta utilizável, etapa 2 ainda não disparada **ou** desmarcado do lote desta execução | Não, até a operação disparar **e** o candidato estar selecionado |
| `avaliado` / `falha_avaliacao` | chamada tentada | Só na execução explícita; ver secção 9 |

Regras de gate no backend (não negociáveis na tela):

1. `decisao.resultado != elegivel` → não chamar, não enviar dado desse candidato.
2. Sem resposta utilizável → `aguardando_resposta`; não chamar.
3. Desmarcado na lista do lote → não chamar; `DecisaoTriagem` intacta; a linha continua `elegivel_pendente_ia` (ou o envelope que já tinha, se já houver `AvaliacaoIa` antiga — a exclusão só vale para **esta** execução).
4. Abrir qualquer tela desta etapa → zero HTTP ao provedor.

Candidato inelegível **com** texto de chatbot mapeado: o texto **não viaja**. A linha mostra o motivo da etapa 1 (ex.: cargo fora da lista). Não há ação habilitada de avaliar nessa pessoa.

### 2.1 Exclusão manual antes do token

Na lista do lote (secção 10.3), cada elegível com resposta utilizável vem **selecionado** por padrão.

O operador desmarca quem não deve ir. Isso:

- é visível (checkbox ou equivalente, rótulo “Incluir nesta avaliação”);
- vale só para a execução que se vai confirmar;
- **não** apaga nem altera `DecisaoTriagem`;
- **não** transforma a pessoa em inelegível;
- **não** persiste como critério duro.

Remarcar inclui de novo na próxima confirmação.

### 2.2 Resposta utilizável

`respostasChatbot` é a lista persistida na importação: `{ colunaMapeada, texto }`. O nome de `colunaMapeada` é o cabeçalho que o operador escolheu; esta spec não prescreve esse nome.

Utilizável se e somente se existe ao menos um item cujo `texto`, depois de:

1. converter para string,
2. `strip`,
3. colapsar whitespace Unicode para um único espaço,

tem comprimento maior que zero.

Casos `aguardando_resposta`:

- o projeto não mapeou nenhuma coluna para `respostasChatbot[]`;
- mapeou, mas esta linha não tem item, ou todos os textos ficam vazios.

Célula só com espaços → não utilizável.

---

## 3. Critérios qualitativos do projeto

Persistidos por `projetoId`. Distintos de `CriteriosDeterministicos`. Duas vagas (dois projetos) têm listas independentes ao mesmo tempo.

### 3.1 Item

| Campo | Obrigatório | Notas |
|---|---|---|
| `criterioId` | sim, ao gravar | gerado na inclusão do item; estável em reordenação e edição de texto |
| `nome` | sim | rótulo curto, único na lista da versão (após trim) |
| `descricao` | sim | o que conta como atendimento, em linguagem da operação |
| `ordem` | sim | inteiro a partir de 1, sem furo após gravar |
| `eliminatorio` | sim | boolean; padrão `false` |

Natureza esperada (exemplos de enunciado, não lista fechada no código): disponibilidade relatada na resposta; experiência relatada na resposta; aderência ao tipo de atendimento descrito no chatbot.

Proibido como conteúdo de negócio desta lista (a tela avisa, secção 3.3): repetir a regra dura de cargo, faixa de idade ou escolaridade para o modelo **rejulgar porta de entrada**.

### 3.2 Operações na tela

Adicionar, editar nome/descrição/flag, remover, reordenar (sobe/desce ou arraste). Lista vazia **pode** existir como rascunho; **não** dispara etapa 2.

**Salvar critérios**:

- persiste o vigente;
- gera novo `versaoId` (ex.: `crt_qual_03`) a cada gravação bem-sucedida, no mesmo espírito da etapa 1;
- guarda snapshot dos `itens` nessa versão.

Mudar o critério **não** reinterpreta avaliações já salvas. `AvaliacaoIa` antiga continua com o `criteriosQualitativosVersaoId` com que foi gerada.

Reexecutar a etapa 2 (disparo novo) é o que gera julgamento novo, com a versão então vigente.

### 3.3 Aviso se a operação colar regra dura

Texto persistente no topo do editor (não bloqueia rascunho):

> Cargo, idade e escolaridade já foram aplicados na triagem. Não cadastre esses critérios aqui para o modelo decidir quem entra. O modelo não reabre a porta de entrada.

Se, ao salvar, `nome` ou `descricao` de algum item (comparados sem acento, em minúsculas) contiver um destes termos — `idade`, `faixa etaria`, `escolaridade`, `ultimo cargo`, `cargos aceitos` — a tela mostra aviso **não silencioso** e pede confirmação:

> Este critério parece repetir regra já aplicada na triagem e não será usado pelo modelo como porta de entrada.

Confirmar grava mesmo assim (a operação manda). Recusar volta ao editor. Em qualquer caso, idade/cargo/escolaridade **não entram no payload** (ADR 007). O aviso não é o gate: o gate é a etapa 1.

### 3.4 Relação com o prompt vigente

O template **injeta** os critérios da versão vigente na montagem. Se `CriteriosQualitativos.versaoId` vigente for diferente de `PromptDoProjeto.criteriosQualitativosVersaoId` da versão de prompt vigente, o disparo é **bloqueado** até o operador salvar o prompt de novo (secção 4.3). Assim cada versão de prompt tem os critérios embutidos de verdade.

Duplicar projeto (etapa 1) copia só critérios **duros**. Critérios qualitativos e prompt do projeto novo começam vazios; a operação os configura. Isso mantém dois projetos diferentes com critérios e prompts diferentes ao mesmo tempo.

---

## 4. Prompt do projeto

Template editável por projeto. É o artefato que consome token. A operação atualiza o texto **sem alterar código e sem novo deploy**.

Não há segundo prompt escondido no código com regra de negócio que a tela não mostre. Instruções técnicas mínimas de formato existem; **aparecem na pré-visualização** (secção 6).

### 4.1 Campos persistidos (`PromptDoProjeto`)

| Campo | Obrigatório | Notas |
|---|---|---|
| `promptId` | sim | identificador da versão (ex.: `prm_03`) |
| `versao` | sim | inteiro monotônico por projeto, começa em 1 |
| `projetoId` | sim | |
| `template` | sim para disparar | texto editável, com delimitadores da secção 4.2 |
| `criteriosQualitativosVersaoId` | sim nesta versão | o vigente **no momento do save** |
| `criteriosEmbutidosSnapshot` | sim | cópia dos `itens` dessa versão de critérios |
| `criadoEm` | sim | data/hora local |

`AvaliacaoIa.promptVersionId` aponta para `promptId`. O texto da avaliação salva **não muda** se o operador editar o template depois.

### 4.2 Delimitadores do template

O editor mostra e o template inicial já traz:

| Delimitador | Conteúdo injetado na montagem |
|---|---|
| `{{candidato_id}}` | `candidatoId` persistido no lote (o mesmo da etapa 1; ver pendência na secção 13) |
| `{{criterios_qualitativos}}` | lista numerada na `ordem`: nome, se é eliminatório, descrição |
| `{{respostas_candidato}}` | só pares mapeados `{ colunaMapeada, texto }` **utilizáveis** daquela pessoa |

Proibido no template vigente (validação ao salvar):

- pedir ao modelo faixa de idade, lista de cargos aceitos ou escolaridade como juízo de entrada;
- pedir cadeia de raciocínio oculta (`think`, “raciocine passo a passo em silêncio”, etc.);
- placeholders que injetariam nome, idade, cargo, escolaridade, cidade, equipe ou status legado.

Se o texto do template (após a mesma normalização visível da etapa 1, só para esta checagem) contém `{{idade}}`, `{{cargo}}`, `{{escolaridade}}` ou pede explicitamente “julgue a idade/o cargo/a escolaridade do candidato”, o save é recusado com:

> O prompt não pode pedir ao modelo que julgue cargo, idade ou escolaridade. Isso já foi decidido na triagem.

### 4.3 Salvar gera versão

Cada save bem-sucedido cria **nova** versão (não sobrescreve o texto da anterior). A vigente passa a ser essa.

Não há “salvar rascunho sem versão” nesta spec: o que está no editor ou é a vigente ou vira vigente ao salvar.

Bloqueio de disparo (mensagem única):

> Os critérios qualitativos mudaram desde a última versão salva do prompt. Salve o prompt para gerar uma versão com os critérios atuais antes de avaliar.

Pré-visualizar **pode** montar com os critérios vigentes mesmo nessa divergência, para o operador ver o que passaria a ser enviado depois do save. Pré-visualizar não chama o LLM.

---

## 5. Template inicial recomendado

Texto a gravar como versão 1 quando o projeto ainda não tem prompt. A operação pode editar depois. Este texto é especificação, não código.

Instruções técnicas de formato (prefixo **visível** na pré-visualização e, se o adaptador HTTP exigir papel `system`, **cópia literal deste mesmo bloco** — nada além):

```
INSTRUÇÕES TÉCNICAS DE FORMATO
Responda somente com um único objeto JSON válido.
Não use markdown, não use cerca de código, não escreva texto antes ou depois do JSON.
O objeto tem exatamente as chaves: perfil, compatibilidade, por_criterio, trechos.
por_criterio é uma lista com um item para cada critério qualitativo informado, na mesma ordem, cada um com: criterioId, nome, resultado, justificativa.
resultado é exatamente um de: atende, atende_parcialmente, nao_atende, sem_informacao.
trechos é uma lista na mesma ordem de por_criterio, cada item com: criterioId, nome, trecho.
Se resultado for sem_informacao, trecho é string vazia.
Não invente chaves extras.
```

Corpo do template (editável na tela):

```
Você avalia respostas de chatbot de uma pessoa que já passou na triagem determinística desta vaga.
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

Saída: somente o objeto JSON.
```

---

## 6. Montagem do payload e pré-visualização

Módulo `avaliacao_ia`. O frontend **não** chama o provedor (ADR 002).

### 6.1 O que entra

Por candidato, e só isso (ADR 007):

- `candidatoId`;
- critérios qualitativos da versão embutida no prompt (nome, descrição, ordem, eliminatório, `criterioId`);
- textos mapeados como respostas utilizáveis (`colunaMapeada` como rótulo da pergunta/coluna + `texto`);
- o template da versão vigente.

### 6.2 O que não entra

- candidatos `inelegivel`;
- elegíveis sem resposta utilizável;
- desmarcados do lote;
- idade, escolaridade, último cargo, cidade, equipe, status legado, justificativa interna, nome;
- colunas da planilha **não** mapeadas para `respostasChatbot[]`;
- a planilha inteira num único prompt;
- vários candidatos no mesmo HTTP.

Injeção de `{{criterios_qualitativos}}` (exemplo de forma, nomes de coluna de resposta **não** aparecem aqui):

```
1. Disponibilidade de horário (eliminatório: não)
   Atende se a resposta indica disponibilidade para os turnos ou janelas descritos na descrição deste critério.
2. Experiência relatada no atendimento (eliminatório: não)
   ...
```

Injeção de `{{respostas_candidato}}`:

```
[coluna mapeada pelo operador: (cabeçalho escolhido na importação)]
(texto da célula)
```

Repetir um bloco desses por item utilizável. Não incluir item vazio. Não inventar cabeçalho.

### 6.3 Pré-visualização

Antes da chamada, a tela monta **localmente** o texto completo que será enviado (prefixo técnico + template já interpolado) para **pelo menos um** candidato selecionado do lote.

A pré-visualização:

- contém os critérios qualitativos da vaga e as respostas daquela pessoa;
- contém `candidatoId`;
- **não** contém a regra de faixa etária, lista de cargos ou escolaridade como pergunta ao modelo;
- **não** contém nome de pessoa;
- é idêntica ao corpo enviado (mais o wrapping HTTP do adaptador estilo OpenAI: `base_url` + `model`; o conteúdo de mensagem é esse texto).

Trocar o candidato da pré-visualização (se houver mais de um selecionado) remonta o texto. Continua sem HTTP ao LLM.

Não enviar a base inteira num único prompt: a pré-visualização é sempre de **uma** pessoa.

---

## 7. Saída do LLM e validação

Contrato com o modelo: **um JSON único**. Planilha, markdown ou texto solto **não** são contrato.

### 7.1 Schema do JSON (modelo)

```json
{
  "perfil": "string",
  "compatibilidade": "compativel",
  "por_criterio": [
    {
      "criterioId": "cq_01",
      "nome": "Disponibilidade de horário",
      "resultado": "atende",
      "justificativa": "string"
    }
  ],
  "trechos": [
    {
      "criterioId": "cq_01",
      "nome": "Disponibilidade de horário",
      "trecho": "string"
    }
  ]
}
```

`compatibilidade` no JSON do modelo é um de `compativel` | `parcial` | `incompativel`. O valor **persistido** é o calculado na secção 8.

`resultado` é um de `atende` | `atende_parcialmente` | `nao_atende` | `sem_informacao`.

### 7.2 Correspondência com os critérios

`por_criterio` e `trechos` têm o mesmo comprimento da lista de critérios da versão embutida.

Para cada critério configurado, existe exatamente um item em cada lista com o mesmo `criterioId`. A ordem é a `ordem` gravada.

Falta, sobra, `criterioId` desconhecido ou `nome` que não coincide com o da versão → resposta **inválida** → `falha_avaliacao` (após o reparo da secção 9).

JSON sem `por_criterio`, ou `por_criterio` que não corresponde aos critérios configurados, é falha de avaliação. Não é `compativel`. Não é inelegível da etapa 1.

### 7.3 Trechos e justificativa

- `resultado = sem_informacao` → `trecho` obrigatoriamente `""`. `sem_informacao` **não** é armazenado nem exibido como `atende`.
- qualquer outro `resultado` → `trecho` não vazio.
- cada `trecho` não vazio tem de ser substring do texto enviado em `{{respostas_candidato}}` (comparação após colapsar whitespace). Trecho que não aparece nas respostas → inválido (o modelo inventou).
- se existe `trecho` não vazio, a `justificativa` tem de conter esse trecho (após colapsar whitespace). Justificativa que não cita o trecho quando há resposta correspondente → **inválida**, não é compatível.

`perfil` obrigatório, string, trim não vazio, no máximo 2000 caracteres após trim. Vazio → inválido.

Não inventar perfil em caso de falha: `AvaliacaoIa.perfil` ausente quando `estado = falha_avaliacao`.

### 7.4 Mapeamento para `AvaliacaoIa` persistida

| JSON / cálculo | Campo persistido |
|---|---|
| `perfil` | `perfil` (só se `sucesso`) |
| regra da secção 8 | `compatibilidade` (só se `sucesso`) |
| `por_criterio` + `trechos` | `justificativasPorCriterio[]` com `criterioId`, `nome`, `resultado`, `justificativa`, `trecho` |
| uso da API | `usoToken.entrada` / `saida` / `total` se o provedor devolveu; senão registrar ausência, não inventar |
| — | `promptVersionId`, `criteriosQualitativosVersaoId` |
| — | `estado`: `sucesso` \| `falha_avaliacao` |
| falha | `erro` com código da secção 12, sem chave, sem nome |

---

## 8. Regra de compatibilidade

Aplicada no backend sobre `por_criterio` já validado. Vale em todos os exemplos desta spec.

Definições:

- critério **informado**: `resultado` ∈ {`atende`, `atende_parcialmente`, `nao_atende`};
- critério **eliminatório**: `eliminatorio = true` na versão embutida.

Regra, nesta ordem:

1. Se algum critério eliminatório tem `nao_atende` → `incompativel`.
2. Senão, se **todos** os critérios informados (e existe pelo menos um informado) são `nao_atende` → `incompativel`.
3. Senão, se **todos** os critérios da versão têm `atende` → `compativel`.
4. Senão → `parcial`.

Consequências explícitas:

- qualquer `nao_atende` **impede** `compativel` (cai em 1, 2 ou 4);
- `sem_informacao` não vira `atende`; se o conjunto não for todo `atende` e não cair em incompativel, o máximo é `parcial`;
- todos `sem_informacao` → `parcial` (informação insuficiente, não nocaute qualitativo);
- mistura `atende` + `atende_parcialmente`, sem `nao_atende` → `parcial`;
- `nao_atende` em critério **não** eliminatório, havendo algum outro informado que não é `nao_atende` → `parcial`.

O JSON do modelo pode trazer `compatibilidade` divergente. Isso **não** é falha se `por_criterio` e `trechos` passaram. Persiste-se o valor calculado. O log da chamada (secção 9.4) registra `compatibilidadeModelo` e `compatibilidadeCalculada` com `candidatoId`, sem nome.

### 8.1 Exemplos da regra (especificação)

Configuração usada nos três primeiros:

| criterioId | nome | eliminatorio |
|---|---|---|
| cq_01 | Disponibilidade de horário | não |
| cq_02 | Experiência relatada no atendimento | não |
| cq_03 | Aderência ao tipo de atendimento | sim |

**A — `compativel`.** cq_01 `atende`, cq_02 `atende`, cq_03 `atende`. Nenhum `nao_atende`. JSON válido na secção 16.1.

**B — `parcial`.** cq_01 `atende`, cq_02 `atende_parcialmente`, cq_03 `atende`. JSON na secção 16.2. Variante: cq_03 `atende`, cq_01 `nao_atende` (não eliminatório), cq_02 `atende` → ainda `parcial`.

**C — `incompativel` por eliminatório.** cq_03 `nao_atende` (eliminatório), demais quaisquer → `incompativel`.

**D — `incompativel` sem flag no que restou informado.** cq_01 `nao_atende`, cq_02 `nao_atende`, cq_03 `sem_informacao` → todos os **informados** são `nao_atende` → `incompativel`.

**E — inválida, não é incompatível.** JSON sem item de cq_02 em `por_criterio`, ou justificativa de cq_01 sem o trecho correspondente. Estado `falha_avaliacao`. Não gravar `compatibilidade`. Não alterar `DecisaoTriagem`. Secção 16.3.

---

## 9. Provedor, token e falha

Seguir ADR 004. Não escolher outro fornecedor.

Variáveis (valores de exemplo da ADR; **chave real jamais** nesta spec):

```
LLM_BASE_URL=https://api.example.com/v1
LLM_API_KEY=
LLM_MODEL=
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
```

Chave só por variável de ambiente. Não versionar valor real. Logs e exemplos desta spec usam `LLM_API_KEY` vazio ou a menção “(ausente)”.

### 9.1 Timeout e tentativas

| Situação | Retentável? | Comportamento |
|---|---|---|
| Timeout (`LLM_TIMEOUT_SECONDS`, padrão 30) | sim, como rede | até `LLM_MAX_RETRIES` novas tentativas do **mesmo** HTTP |
| Falha de rede, DNS, conexão recusada, HTTP 429/502/503/504 | sim | idem; backoff simples (espera de 1s, depois 2s) entre tentativas |
| HTTP 401/403 (chave inválida ou ausente no provedor) | não | `falha_avaliacao` naquele candidato; não vazar o valor da chave |
| HTTP 400 de schema da API | não | falha naquele candidato |
| Corpo não-JSON ou JSON que não passa na secção 7 | não como rede | **uma** chamada de reparo (secção 9.2); se falhar, `falha_avaliacao` |
| `LLM_API_KEY` vazia ou `LLM_BASE_URL` / `LLM_MODEL` vazios | não chama | lote inteiro recusado **antes** de qualquer HTTP; tela explica falta de configuração |

`LLM_MAX_RETRIES=2` significa no máximo duas retentativas após a primeira tentativa de rede, para **aquele** candidato. Uma resposta inválida **não** invalida os demais do lote: cada um tem seu HTTP.

Indisponibilidade do provedor **não altera** `DecisaoTriagem`. Inelegível continua inelegível; elegível continua elegível. O envelope vira `falha_avaliacao` só para quem teve chamada tentada.

### 9.2 Reparo de JSON

Se o corpo da primeira resposta (já após retries de rede bem-sucedidos) não parseia ou não valida o schema:

1. Uma segunda chamada, **só daquele candidato**, enviando o mesmo prefixo técnico + o JSON rejeitado delimitado + a frase: `Corrija para o schema exigido. Responda somente com o objeto JSON. Não invente fatos fora das respostas originais.`
2. As respostas originais e os critérios **entram de novo** nesse reparo (o modelo precisa do contexto). Continua um candidato por HTTP.
3. Se o reparo também for inválido → `falha_avaliacao`, código `json_invalido`. Sem perfil inventado.

Não há terceira chamada de reparo.

### 9.3 Estado `falha_avaliacao`

Resposta inválida, timeout esgotado, erro HTTP não retentável ou chave/config ausente no disparo **por candidato já enviado**:

- **não** marca `compativel`;
- **não** marca `incompativel` como julgamento (não há `compatibilidade` persistida);
- **não** marca inelegível da etapa 1;
- estado `falha_avaliacao`;
- a operação pode **rodar de novo** aquele candidato (selecioná-lo num lote posterior).

Falha distinta de incompatível na tela (secção 10.5).

### 9.4 Registro de cada chamada

Persistir por tentativa consolidada (a chamada “de negócio”, incluindo reparo se houve), com `candidatoId` e `projetoId`, **sem nome**, **sem valor de chave**:

| Campo | Obrigatório |
|---|---|
| `candidatoId` | sim |
| `promptVersionId` | sim |
| `modeloConfigurado` | sim (`LLM_MODEL`; se vazio, a execução nem parte) |
| `tokensEntrada` / `tokensSaida` / `tokensTotal` | se o provedor devolveu uso; senão `null` e nota `uso_nao_reportado` |
| `statusChamada` | `sucesso` \| `falha_rede` \| `json_invalido` \| `erro_http` \| `timeout` \| `config_ausente` |
| `tentativasRede` | sim |
| `houveReparoJson` | sim, boolean |
| `compatibilidadeModelo` / `compatibilidadeCalculada` | se JSON validou |

A tela, **ao final** do lote, mostra a soma de `tokensTotal` conhecidos e quantos registros não tiveram uso reportado. Não inventar soma.

### 9.5 Confirmação antes de gastar token

O lote **não dispara** sem a operação ter visto **quantos** candidatos serão enviados (contagem da seleção atual).

Não é obrigatório estimar token **antes**. É obrigatório mostrar a contagem e o texto:

> Esta execução envia N candidato(s) ao modelo, um por chamada. Quem está inelegível, aguardando resposta ou desmarcado não será enviado.

N = selecionados com `elegivel` + resposta utilizável, depois do gate. Se N = 0, recusar com a mensagem da secção 12. Zero HTTP.

Não enviar inelegíveis mesmo que a UI falhe: o backend recusa item a item.

---

## 10. Telas

Forma: aplicação web local (ADR 001). Sem login. Sem projeto corrente, as ações desta etapa recusam com a mensagem já da etapa 1: “Abra ou crie um projeto para continuar.”

Navegação do orquestrador, passos 5–7. O botão **Avaliar trajetória** aparece desabilitado onde o orquestrador o colocou; esta spec não desenha ação nova para ele.

### 10.1 Critérios qualitativos do projeto

Lista dos itens (nome, descrição, eliminatório, ordem). Ações: adicionar, editar, remover, reordenar, salvar.

Aviso da secção 3.3 sempre visível. Confirmação extra se parecer regra dura.

Estado vazio: CTA para adicionar o primeiro critério. Não há disparo de LLM nesta tela.

### 10.2 Editor do prompt e pré-visualização

- área de texto do template (versão vigente carregada);
- lista das versões anteriores (id, data, `versao`; só leitura do texto antigo — restaurar = copiar para o editor e **salvar**, o que gera versão nova, não reescreve a antiga);
- botão salvar (nova versão);
- pré-visualização: seletor com pelo menos um elegível com resposta selecionável no lote; se não houver nenhum, a pré-visualização mostra “Não há candidato com resposta utilizável para montar o texto.” e o corpo vazio;
- a pré-visualização exibe o prefixo técnico + o template interpolado.

Não dispara LLM.

### 10.3 Lista para o lote (elegíveis, aguardando, inelegíveis)

Uma lista do lote do projeto corrente, três blocos ou um filtro equivalente. Colunas mínimas: rótulo (`nomeExibicao` se mapeado, senão `candidatoId` + `linhaOrigem`), estado, detalhe.

| Bloco | Selecionável para envio | Detalhe na linha |
|---|---|---|
| Elegíveis com resposta utilizável | sim (padrão marcado) | “Incluir nesta avaliação”; se já houver `AvaliacaoIa` de sucesso, indicar que um novo disparo gera nova avaliação e **não reescreve** a anterior (a vigente de exibição passa a ser a mais recente com `sucesso` ou `falha_avaliacao`) |
| Elegíveis aguardando resposta | não | “Aguardando resposta”; sem checkbox de envio |
| Inelegíveis | não | motivos da etapa 1 (mensagens já especificadas lá); **visível**; não selecionável |

Inelegível nunca aparece como “pronto para IA”.

Barra: **Revisar lote e avaliar** — só habilita se houver pelo menos um selecionado **e** critérios salvos **e** prompt vigente **e** mapeamento de chatbot **e** critérios alinhados à versão do prompt. Senão, o botão explica o que falta (não chama rede).

### 10.4 Confirmação do lote

Tela ou passo modal **depois** de “Revisar lote e avaliar”, **antes** do HTTP:

- N = quantidade que será enviada;
- lista resumida dos `candidatoId` (e rótulo se houver) que irão;
- modelo configurado (`LLM_MODEL`), sem chave;
- texto da secção 9.5;
- **Confirmar envio** / **Voltar**.

Confirmar dispara o backend. Fechar a confirmação sem confirmar → zero chamada.

Progresso: por candidato, enviado / avaliado / falhou. Um inválido não cancela os demais.

### 10.5 Resultado (composição 1 + 2)

Envelope já definido no contrato. Esta spec preenche o que é da etapa 2.

| `resultadoExibicao` | O que a linha mostra |
|---|---|
| `inelegivel` | decisão e motivos da etapa 1; **sem** perfil de LLM |
| `aguardando_resposta` | “Aguardando resposta”; sem perfil |
| `elegivel_pendente_ia` | “Elegível na triagem — avaliação por IA não executada” (ou desmarcado na última execução) |
| `avaliado` | `perfil`; `compatibilidade` (`compatível` / `parcial` / `incompatível` na UI, glossário; nunca `contratado`); por critério: nome, resultado, justificativa, trecho; versão do prompt (`promptId` / `versao` / data); tokens daquela avaliação se houver |
| `falha_avaliacao` | rótulo **Falha de avaliação**, distinto de incompatível; código/mensagem da secção 12; ação **Avaliar de novo** (abre a lista com essa pessoa selecionada); triagem intacta |

Exibição de `sem_informacao`: texto “Sem informação nas respostas”. **Não** usar cor, ícone ou coluna de “atende”. **Não** contar como critério atendido em resumo numérico, se houver.

Filtro: todos / inelegível / aguardando / pendente / avaliado / falha / compatível / parcial / incompatível.

Tokens do lote: após uma execução, faixa “Tokens desta execução: entrada X, saída Y, total Z” (somas do que o provedor reportou) + aviso se algum registro veio sem uso.

Botão **Avaliar trajetória**: visível no mapa, desabilitado, sem request.

### 10.6 O que esta spec não desenha

- botão ativo de trajetória;
- editor de critérios duros (etapa 1);
- funil Excel (ADR 005);
- tela de login.

---

## 11. Persistência e contratos desta etapa

Não altera `specs/03-contratos-compartilhados.md`. Preenche o que o contrato deixou para o agente 2.

SQLite (ADR 003). Fecha e reabre: critérios qualitativos, versões de prompt e `AvaliacaoIa` continuam.

### 11.1 `CriteriosQualitativos` (exemplo)

```json
{
  "projetoId": "prj_01",
  "versaoId": "crt_qual_03",
  "itens": [
    {
      "criterioId": "cq_01",
      "nome": "Disponibilidade de horário",
      "descricao": "Atende se a resposta indica disponibilidade para turnos ou janelas descritos neste critério.",
      "ordem": 1,
      "eliminatorio": false
    },
    {
      "criterioId": "cq_02",
      "nome": "Experiência relatada no atendimento",
      "descricao": "Atende se a resposta relata experiência de atendimento alinhada ao que a descrição pede. Não inventar cargo ou tempo que não esteja no texto.",
      "ordem": 2,
      "eliminatorio": false
    },
    {
      "criterioId": "cq_03",
      "nome": "Aderência ao tipo de atendimento",
      "descricao": "Atende se a resposta demonstra aderência ao tipo de atendimento descrito. Ausência de informação não conta como atendimento.",
      "ordem": 3,
      "eliminatorio": true
    }
  ]
}
```

O contrato compartilhado descreve “identificador + enunciado”. Nesta spec, enunciado = `nome` + `descricao`; `eliminatorio` e `ordem` são detalhe do dono.

### 11.2 `PromptDoProjeto` (exemplo de metadado, template na secção 5)

```json
{
  "promptId": "prm_03",
  "versao": 3,
  "projetoId": "prj_01",
  "criteriosQualitativosVersaoId": "crt_qual_03",
  "criadoEm": "2026-09-22T10:00:00-03:00"
}
```

O campo `template` é o texto da secção 5 (ou a edição da operação). `criteriosEmbutidosSnapshot` copia `itens` de `crt_qual_03`.

### 11.3 `AvaliacaoIa` sucesso (esboço)

```json
{
  "candidatoId": "12:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "projetoId": "prj_01",
  "promptVersionId": "prm_03",
  "criteriosQualitativosVersaoId": "crt_qual_03",
  "perfil": "A pessoa relata disponibilidade em horário comercial e experiência prévia em atendimento por chat, com ênfase em fila de suporte.",
  "compatibilidade": "compativel",
  "justificativasPorCriterio": [],
  "usoToken": { "entrada": 1180, "saida": 420, "total": 1600 },
  "estado": "sucesso"
}
```

`candidatoId` do exemplo é o formato da spec de triagem (pendência UUID, secção 13). `justificativasPorCriterio` completo está na secção 16.1. O hash é ilustrativo.

Nova execução bem-sucedida **acrescenta** registro; não reescreve o JSON da avaliação anterior. A tela de resultado mostra a mais recente.

### 11.4 Reimportação e reexecução da etapa 1

A etapa 1 já substitui o lote e apaga `DecisaoTriagem` do projeto na reimportação.

Esta spec: a reimportação **também apaga** `AvaliacaoIa` e os registros de chamada daquele `projetoId`. O lote mudou; avaliação antiga não pode parecer vigente.

Reexecutar só a triagem (sem reimportar): `DecisaoTriagem` é substituída (etapa 1). `AvaliacaoIa` **não** é apagada. O envelope de leitura: se a nova decisão é `inelegivel`, mostra inelegível com motivos (a avaliação antiga não é o resultado principal). Se continua `elegivel`, a avaliação existente permanece exibível até um novo disparo da etapa 2.

### 11.5 O que esta etapa não preenche

Não recalcula `DecisaoTriagem`. Não executa `PedidoTrajetoria`. Não lê headline, resumo ou trajetória de cargos.

---

## 12. Erros

| Situação | Comportamento |
|---|---|
| Sem projeto aberto | Recusa. “Abra ou crie um projeto para continuar.” |
| Sem mapeamento de coluna de chatbot | Recusa do disparo e do botão da lista. “Mapeie ao menos uma coluna de resposta do chatbot na importação. Sem esse mapeamento a avaliação por IA não roda.” |
| Critérios qualitativos vazios | Recusa do disparo. “Cadastre ao menos um critério qualitativo da vaga.” |
| Sem prompt vigente | Recusa. “Salve um prompt do projeto antes de avaliar.” |
| Critérios e prompt desalinhados | Recusa. Mensagem da secção 4.3 |
| N = 0 na confirmação | Recusa. “Nenhum candidato elegível com resposta utilizável está selecionado para envio.” |
| `LLM_API_KEY` ou `LLM_BASE_URL` ou `LLM_MODEL` vazios | Recusa do lote, zero HTTP. “A avaliação por IA não está configurada. Defina as variáveis de ambiente do modelo (a chave não aparece nesta tela).” |
| Inelegível no pedido | Backend ignora / não chama; se o pedido era só dele, responde sem chamada e a tela permanece nos motivos da etapa 1 |
| JSON inválido após reparo | `falha_avaliacao`, `json_invalido`. Triagem intacta |
| Trecho fora das respostas | `falha_avaliacao`, `trecho_nao_encontrado` |
| Justificativa sem citar trecho | `falha_avaliacao`, `justificativa_sem_trecho` |
| Timeout esgotado | `falha_avaliacao`, `timeout` |
| Rede esgotada | `falha_avaliacao`, `falha_rede` |
| Item vazio ao incluir critério | Ignorar, avisar “Item vazio ignorado.” |
| Nome de critério duplicado na lista | Recusar o save. “Já existe um critério com este nome.” |

Mensagens **não** incluem o valor de `LLM_API_KEY`.

---

## 13. Pendência herdada (`candidatoId`)

O contrato compartilhado e a ADR 003 definem `candidatoId` como UUID. A spec da etapa 1, no conflito, usa `{linhaOrigem}:{sha256hex}`.

**Esta spec não reabre a disputa e não altera o contrato.** Usa o `candidatoId` **já persistido** no lote (`CandidatoImportado`). O payload do LLM e o log usam esse mesmo valor. Nome, se mapeado, só no envelope local.

Impacto registrado em `specs/history.md`.

Nenhum outro conflito impede as regras deste prompt. Esta spec não altera `specs/03-contratos-compartilhados.md` nem `specs/sprint-1/triagem-deterministica.md`.

---

## 14. Critérios de aceite (Given / When / Then)

Não são testes automatizados. O implementador pode traduzi-los depois.

### CA-01 — Inelegível por cargo não gera chamada

Given um candidato com `DecisaoTriagem.resultado = inelegivel` e motivo `cargo_fora_da_lista`  
And essa linha tem `respostasChatbot` com texto não vazio  
When a operação dispara a avaliação por IA do lote  
Then não há chamada HTTP ao provedor para esse `candidatoId`  
And a tela mostra o motivo da etapa 1  
And o candidato não está selecionável para envio

### CA-02 — Elegível sem resposta aguarda

Given um candidato `elegivel` sem resposta utilizável  
When a operação dispara a avaliação por IA  
Then não há chamada para esse `candidatoId`  
And o envelope é `aguardando_resposta`

### CA-03 — Alterar o prompt não muda avaliação salva

Given uma `AvaliacaoIa` persistida com `promptVersionId = prm_03` e um `perfil` P  
When o operador edita o template e salva `prm_04`  
Then o registro antigo permanece com `promptVersionId = prm_03` e `perfil` P inalterado

### CA-04 — Pré-visualização tem critérios e respostas, não faixa etária

Given critérios qualitativos vigentes e um elegível com respostas mapeadas  
And o projeto tem faixa de idade ativa na etapa 1  
When o operador abre a pré-visualização desse candidato  
Then o texto contém os nomes e descrições dos critérios qualitativos  
And contém os textos das respostas mapeadas daquela pessoa  
And não contém a regra de faixa etária como pergunta ao modelo  
And não contém lista de cargos aceitos nem escolaridade como juízo pedido ao modelo

### CA-05 — JSON sem `por_criterio` correspondente é falha

Given critérios `cq_01`, `cq_02`, `cq_03` na versão embutida  
And o provedor devolve JSON sem item de `cq_02` em `por_criterio` (e o reparo também)  
When a resposta é validada  
Then `estado = falha_avaliacao`  
And não há `compatibilidade` persistida  
And `DecisaoTriagem` permanece `elegivel`

### CA-06 — `sem_informacao` não aparece como atendido

Given um critério com `resultado = sem_informacao` numa avaliação `sucesso`  
When a tela de resultado é exibida  
Then o critério mostra “Sem informação nas respostas”  
And não é exibido como critério atendido  
And esse resultado não conta como `atende` na regra da secção 8

### CA-07 — Erro do provedor deixa a triagem intacta

Given `DecisaoTriagem.resultado = elegivel`  
When o provedor responde HTTP 503 até esgotar retries  
Then `DecisaoTriagem` permanece igual  
And o envelope da etapa 2 é `falha_avaliacao`  
And a pessoa não é marcada `inelegivel` nem `compativel`

### CA-08 — Dois projetos, critérios e prompts distintos

Given projeto A com critério “Disponibilidade” e prompt versão 1  
And projeto B com critério “Turno noturno” e prompt versão 2, diferente do texto de A  
When os dois existem ao mesmo tempo  
Then salvar em A não altera os itens nem o template vigente de B

### CA-09 — Chave não aparece em log nem em exemplo operacional

Given uma chamada (sucesso ou falha)  
When o registro da chamada é persistido e a tela de erro de configuração é mostrada  
Then o valor de `LLM_API_KEY` não é gravado nem exibido  
And os exemplos desta spec não trazem chave real

### CA-10 — Exclusão manual não apaga a triagem e não gasta token

Given um elegível com resposta utilizável desmarcado na lista do lote  
When a operação confirma o envio  
Then não há chamada para esse `candidatoId`  
And `DecisaoTriagem` permanece `elegivel`

### CA-11 — Sem mapeamento a etapa 2 não roda

Given um projeto cuja importação não mapeou nenhuma coluna para `respostasChatbot[]`  
When o operador tenta disparar a avaliação por IA  
Then a execução é recusada com a mensagem da secção 12  
And zero HTTP

### CA-12 — Uma chamada por candidato; inválido não mata o lote

Given dois elegíveis com resposta, selecionados  
And o primeiro devolve JSON inválido após reparo e o segundo devolve JSON válido  
When o lote termina  
Then o primeiro está `falha_avaliacao`  
And o segundo está `avaliado`  
And houve HTTP separado para cada um

### CA-13 — Confirmação mostra N antes do envio

Given três elegíveis com resposta selecionados  
When o operador aciona avaliar  
Then vê a confirmação com N = 3 **antes** de qualquer HTTP ao LLM  
And só após Confirmar envio as chamadas partem

### CA-14 — Tokens ao final do lote

Given um lote em que o provedor reportou uso em todas as chamadas  
When a execução termina  
Then a tela mostra a soma dos tokens de entrada, saída e total dessa execução

### CA-15 — Abrir a tela não dispara

Given elegíveis com resposta e configuração completa  
When o operador só abre as telas de critérios, prompt, lista ou resultado  
Then não há HTTP ao provedor

### CA-16 — `compativel` exige todos `atende`

Given `por_criterio` válido com um `atende_parcialmente` e o restante `atende`, nenhum `nao_atende`  
When a regra da secção 8 é aplicada  
Then `compatibilidade` persistida é `parcial`  
And não é `compativel`

### CA-17 — Eliminatório `nao_atende` vira incompatível

Given critério `cq_03` com `eliminatorio = true` e `resultado = nao_atende`  
When a regra da secção 8 é aplicada  
Then `compatibilidade` persistida é `incompativel`

### CA-18 — Justificativa sem trecho é falha, não compatível

Given `resultado = atende`, `trecho` não vazio presente nas respostas, e `justificativa` que não contém esse trecho, inclusive após reparo  
When a validação corre  
Then `falha_avaliacao` com `justificativa_sem_trecho`  
And não persiste `compativel`

### CA-19 — Configuração de ambiente vazia

Given `LLM_API_KEY` vazia  
When a etapa 2 é disparada  
Then não há chamada  
And a tela explica a falta de configuração sem mostrar valor de chave

### CA-20 — Trajetória permanece desabilitada

Given a navegação da primeira entrega  
When o operador vê o botão **Avaliar trajetória**  
Then ele está desabilitado, informa sprint posterior e não dispara modelo  
And esta etapa não o habilita

### CA-21 — Inelegível visível e não selecionável

Given um inelegível no lote  
When a lista da etapa 2 é exibida  
Then a linha está visível com os motivos da etapa 1  
And não há controle de inclusão no envio habilitado nessa linha

---

## 15. Rastreabilidade

Requisito → regra de envio → campo de tela → campo do JSON → estado persistido → critério de aceite.

| ID | Requisito | Regra de envio | Campo de tela | JSON / persistido | Aceite |
|---|---|---|---|---|---|
| R1 | Inelegível não gasta token | Secção 2 gate 1 | Lista inelegíveis; motivos etapa 1 | sem `AvaliacaoIa` nova; `DecisaoTriagem` | CA-01, CA-21 |
| R2 | Elegível sem resposta aguarda | Secção 2.2 | Bloco aguardando | sem chamada | CA-02 |
| R3 | Disparo explícito; exclusão manual | Secção 2.1, 9.5, 10.4 | Checkbox; confirmação N | só selecionados | CA-10, CA-13, CA-15 |
| R4 | Critérios qualitativos por projeto | Secção 3 | Editor de critérios | `CriteriosQualitativos` | CA-08 |
| R5 | Aviso de regra dura colada | Secção 3.3 | Aviso + confirmação | payload ainda sem idade/cargo/escolaridade | CA-04 |
| R6 | Prompt versionado, editável sem deploy | Secção 4 | Editor + versões | `PromptDoProjeto`; `AvaliacaoIa.promptVersionId` | CA-03, CA-08 |
| R7 | Pré-visualização = texto enviado | Secção 6 | Pré-visualização | interpolação `{{...}}` | CA-04 |
| R8 | JSON único com perfil, compatibilidade, por critério, trechos | Secção 7 | Resultado avaliado | schema secção 7.1 | CA-05, 16.1–16.3 |
| R9 | Correspondência 1:1 com critérios | Secção 7.2 | — | `por_criterio` | CA-05 |
| R10 | `sem_informacao` ≠ atendido | Secção 7.3 e 8 | “Sem informação nas respostas” | `resultado` | CA-06 |
| R11 | Trecho literal e justificativa que cita | Secção 7.3 | Trecho + justificativa | `trechos` | CA-18 |
| R12 | Regra de compatibilidade | Secção 8 | Compatível / parcial / incompatível | `compatibilidade` calculada | CA-16, CA-17 |
| R13 | Provedor por env; timeout; retry de rede | Secção 9 | Modelo visível; chave não | registro da chamada | CA-07, CA-09, CA-19 |
| R14 | Falha ≠ incompatível; triagem intacta | Secção 9.3 | Falha de avaliação | `estado = falha_avaliacao` | CA-05, CA-07, CA-18 |
| R15 | Uma chamada por candidato; tokens ao final | Secção 9.4–9.5 | Soma de tokens | `usoToken` | CA-12, CA-14 |
| R16 | Sem mapeamento não roda | Secção 2.2, 12 | Erro de mapeamento | zero HTTP | CA-11 |
| R17 | Dois projetos independentes | Secção 3, 4 | Telas por projeto corrente | `projetoId` | CA-08 |
| R18 | Payload mínimo (ADR 007) | Secção 6.1–6.2 | Pré-visualização | só id + critérios + respostas | CA-04 |
| R19 | Trajetória fora | Cabeçalho; 10.5 | Botão desabilitado | sem `PedidoTrajetoria` | CA-20 |
| R20 | Avaliação antiga presa à versão | Secção 3.2, 4.1, 11.3 | Histórico de versão no resultado | ids de versão | CA-03 |

Validação e erro: secções 7, 9 e 12. Given/When/Then: secção 14. Template e exemplos: secções 5 e 16.

---

## 16. Exemplos de resposta do modelo

Especificação, não implementação. Textos de resposta são ilustrativos; cabeçalhos de coluna não são nomes reais observados em CSV.

Critérios embutidos: os três da secção 11.1. `candidatoId` ilustrativo no formato da etapa 1.

Texto enviado em `{{respostas_candidato}}` para 16.1 e 16.2:

```
[coluna mapeada pelo operador: (definida na importação)]
Consigo trabalhar em horário comercial, das 8h às 18h. Atendi fila de chat de suporte por dois anos e me identifico com atendimento consultivo por escrito.
```

### 16.1 Compatível (JSON válido)

```json
{
  "perfil": "A pessoa declara disponibilidade em horário comercial e relata dois anos em fila de chat de suporte, com identificação com atendimento consultivo por escrito.",
  "compatibilidade": "compativel",
  "por_criterio": [
    {
      "criterioId": "cq_01",
      "nome": "Disponibilidade de horário",
      "resultado": "atende",
      "justificativa": "A resposta afirma disponibilidade em horário comercial: \"Consigo trabalhar em horário comercial, das 8h às 18h.\""
    },
    {
      "criterioId": "cq_02",
      "nome": "Experiência relatada no atendimento",
      "resultado": "atende",
      "justificativa": "A resposta relata experiência em fila de chat: \"Atendi fila de chat de suporte por dois anos e me identifico com atendimento consultivo por escrito.\""
    },
    {
      "criterioId": "cq_03",
      "nome": "Aderência ao tipo de atendimento",
      "resultado": "atende",
      "justificativa": "A resposta cita atendimento consultivo por escrito: \"Atendi fila de chat de suporte por dois anos e me identifico com atendimento consultivo por escrito.\""
    }
  ],
  "trechos": [
    {
      "criterioId": "cq_01",
      "nome": "Disponibilidade de horário",
      "trecho": "Consigo trabalhar em horário comercial, das 8h às 18h."
    },
    {
      "criterioId": "cq_02",
      "nome": "Experiência relatada no atendimento",
      "trecho": "Atendi fila de chat de suporte por dois anos e me identifico com atendimento consultivo por escrito."
    },
    {
      "criterioId": "cq_03",
      "nome": "Aderência ao tipo de atendimento",
      "trecho": "Atendi fila de chat de suporte por dois anos e me identifico com atendimento consultivo por escrito."
    }
  ]
}
```

Persistir `compatibilidade = compativel` (regra 3 da secção 8).

### 16.2 Parcial (JSON válido)

Mesmas respostas. Julgamento: disponibilidade atende; experiência atende em parte; aderência atende.

```json
{
  "perfil": "A pessoa tem horário comercial disponível e relata passagem por fila de chat, com ênfase em atendimento por escrito.",
  "compatibilidade": "parcial",
  "por_criterio": [
    {
      "criterioId": "cq_01",
      "nome": "Disponibilidade de horário",
      "resultado": "atende",
      "justificativa": "Há declaração explícita de horário comercial: \"Consigo trabalhar em horário comercial, das 8h às 18h.\""
    },
    {
      "criterioId": "cq_02",
      "nome": "Experiência relatada no atendimento",
      "resultado": "atende_parcialmente",
      "justificativa": "Há relato de fila de chat, sem detalhar complexidade além disso: \"Atendi fila de chat de suporte por dois anos e me identifico com atendimento consultivo por escrito.\""
    },
    {
      "criterioId": "cq_03",
      "nome": "Aderência ao tipo de atendimento",
      "resultado": "atende",
      "justificativa": "A pessoa se identifica com atendimento consultivo por escrito: \"Atendi fila de chat de suporte por dois anos e me identifico com atendimento consultivo por escrito.\""
    }
  ],
  "trechos": [
    {
      "criterioId": "cq_01",
      "nome": "Disponibilidade de horário",
      "trecho": "Consigo trabalhar em horário comercial, das 8h às 18h."
    },
    {
      "criterioId": "cq_02",
      "nome": "Experiência relatada no atendimento",
      "trecho": "Atendi fila de chat de suporte por dois anos e me identifico com atendimento consultivo por escrito."
    },
    {
      "criterioId": "cq_03",
      "nome": "Aderência ao tipo de atendimento",
      "trecho": "Atendi fila de chat de suporte por dois anos e me identifico com atendimento consultivo por escrito."
    }
  ]
}
```

Persistir `parcial` (regra 4). Mesmo se o modelo tivesse escrito `compativel`, persistiria `parcial`.

### 16.3 Inválida (não é incompatível)

O provedor devolve (e o reparo também):

```json
{
  "perfil": "Perfil amplo, parece experiente em várias áreas.",
  "compatibilidade": "compativel",
  "por_criterio": [
    {
      "criterioId": "cq_01",
      "nome": "Disponibilidade de horário",
      "resultado": "atende",
      "justificativa": "Tem disponibilidade."
    }
  ],
  "trechos": [
    {
      "criterioId": "cq_01",
      "nome": "Disponibilidade de horário",
      "trecho": "Consigo trabalhar em horário comercial, das 8h às 18h."
    }
  ]
}
```

Por quê é inválida:

- `por_criterio` não corresponde a `cq_02` e `cq_03`;
- a justificativa de cq_01 não contém o trecho;
- `perfil` inventa “várias áreas” fora das respostas (o gate operacional desta spec, porém, é schema + trecho + citação; o template já proíbe inventar).

Efeito: `falha_avaliacao`, código `json_invalido` (falta de correspondência) e, se só a justificativa falhasse, `justificativa_sem_trecho`. **Não** persistir `compativel`. **Não** marcar inelegível. Permitir novo disparo.

---

## 17. Fora desta spec

- Implementar cliente HTTP, SDK, tela, `.env` real, migração
- Fine-tuning, embedding, RAG, segundo modelo de trajetória
- Mandar idade, lista de cargos ou escolaridade para o LLM decidir a etapa 1
- Usar `Status` histórico, `contratado` ou `predict_proba` como rótulo
- Leitura de resumo, headline ou trajetória de cargos
- Afirmar que o CSV legado já tem colunas de resposta (não foram lidas: não há arquivo local)
- Escolher fornecedor de LLM por cima da ADR 004
- Habilitar `avaliar_trajetoria`
- Autenticação, JWT, papéis

## 18. Definition of done da spec

- [x] Estados de quem entra na chamada, sem token nos três primeiros; exclusão manual; disparo explícito
- [x] Critérios qualitativos persistidos por projeto, com aviso de regra dura; versões que não reescrevem avaliação antiga
- [x] Prompt editável, versionado, com delimitadores; pré-visualização; sem prompt de negócio escondido
- [x] Template inicial no markdown
- [x] JSON único, regra de compatibilidade documentada com exemplos, `sem_informacao` ≠ `atende`
- [x] Provedor da ADR 004: env, timeout, retry de rede vs JSON, tokens, uma chamada por candidato
- [x] Telas de critérios, prompt, lista, confirmação, resultado e falha distinta; trajetória não habilitada
- [x] Given/When/Then mínimos do prompt e rastreabilidade
- [x] Três exemplos (compatível, parcial, inválida)
- [x] Conflito de `candidatoId` só em `specs/history.md`; contratos e spec de triagem intocados
- [x] Sem implementação de produto
