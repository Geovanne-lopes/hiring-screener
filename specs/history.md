# Histórico do produto (specs)

## Estado atual (2026-09-23)

- Legado analisado no repositório `data-visualization-carrefour/data-visualisation-carrefour`.
- Sistema novo em implementação na sprint 1 (`apps/api`, `apps/web`).
- Spec da etapa 1 escrita: `specs/sprint-1/triagem-deterministica.md`.
- Spec da etapa 2 escrita: `specs/sprint-1/avaliacao-ia-chatbot.md`.
- Spec da etapa 3 escrita: `specs/sprint-2/trajetoria-profissional.md` (sprint posterior; **não** entra na primeira entrega).
- Revisão de operação especificada e **ainda não implementada**: `specs/revisao/01-job-description.md`, `specs/revisao/02-analise-por-pergunta.md`, `specs/revisao/03-rankings.md`. Onde divergir da etapa 2, a revisão prevalece no disparo novo. A triagem dura não muda.
- Não há CSV/XLSX local no disco analisado; colunas de texto de chatbot, resumo e headline não foram inventadas.

### 2026-09-22 — Implementador sprint 1: `candidatoId` composto (não UUID)

**Escolha.** O contrato e a ADR 003 pedem UUID; a spec de triagem e esta pendência mandam prevalecer `{linhaOrigem}:{sha256hex}` nesta entrega. O código de importação gera esse formato e não gera UUID para `candidatoId`.

**Onde.** Comentário operacional deste histórico, sem reabrir a arquitetura nem reescrever o contrato.

## O que este agente entregou

| Arquivo | Conteúdo |
|---|---|
| `specs/00-visao-produto.md` | Recorte da primeira entrega, etapas 1–2, reserva da 3 |
| `specs/01-legado-e-gaps.md` | Comportamento real, bugs, código morto, o que não preservar |
| `specs/02-arquitetura.md` | Web local, stack, diagrama, aceite de arquitetura |
| `specs/03-contratos-compartilhados.md` | Tipos entre etapas |
| `specs/glossario.md` | Vocabulário que substitui `contratado` / `fora do perfil` |
| `specs/adr/001-forma-do-produto-aplicacao-web-local.md` | Tela web local, sem terminal como interface |
| `specs/adr/002-stack-tecnologica.md` | React/Vite + FastAPI + módulos isolados |
| `specs/adr/003-persistencia-sqlite.md` | SQLite; Excel não é banco |
| `specs/adr/004-provedor-llm-configuravel.md` | Env, timeout, retry, schema, tokens |
| `specs/adr/005-funil-excel-fora-do-fluxo-principal.md` | Funil legado fora da 1ª entrega |
| `specs/adr/006-mapeamento-ultimo-cargo.md` | Operador mapeia; `Cargo` se for a única |
| `specs/adr/007-privacidade-e-seguranca-local.md` | Payload mínimo; sem JWT; nome fora do prompt |

## Próximos agentes (chats separados)

1. ~~`prompts/sdd/01-agente-triagem-deterministica.md` → `specs/sprint-1/triagem-deterministica.md`~~ (entregue)
2. ~~`prompts/sdd/02-agente-avaliacao-ia-chatbot.md` → `specs/sprint-1/avaliacao-ia-chatbot.md`~~ (entregue)
3. ~~`prompts/sdd/03-agente-trajetoria-profissional.md` → `specs/sprint-2/trajetoria-profissional.md`~~ (entregue; sprint posterior, sem puxar para a 1ª entrega)

Nenhum desses agentes implementa produto, chama API de LLM ou gera tela.

## O que o agente 1 (triagem determinística) entregou

| Arquivo | Conteúdo |
|---|---|
| `specs/sprint-1/triagem-deterministica.md` | Tela de critérios duros, importação, comparação de cargo/idade/escolaridade, `DecisaoTriagem`, erros, Given/When/Then, rastreabilidade |

Não editou contratos, ADRs, visão, legado, arquitetura nem glossário. Não criou spec de IA nem de trajetória. Não implementou produto.

## O que o agente 2 (avaliação por IA do chatbot) entregou

| Arquivo | Conteúdo |
|---|---|
| `specs/sprint-1/avaliacao-ia-chatbot.md` | Quem entra na chamada, critérios qualitativos, prompt versionado, template inicial, JSON de saída, regra de compatibilidade, provedor/token/falha, telas, Given/When/Then, rastreabilidade, exemplos |

Não editou contratos, ADRs, visão, legado, arquitetura, glossário nem a spec de triagem. Não criou spec de trajetória. Não implementou produto. Não inventou nomes de coluna de resposta (CSV local ausente; legado só conta `Enviado` / `Respondido` / `Elegível`).

Detalhe do dono, sem reescrever o contrato: `CriteriosQualitativos.itens` = `criterioId` + `nome` + `descricao` + `ordem` + `eliminatorio` (o contrato pedia identificador + enunciado). `AvaliacaoIa` guarda o JSON validado e a compatibilidade **calculada** no backend. Reimportação do lote (já apaga `DecisaoTriagem` na etapa 1) também apaga `AvaliacaoIa` daquele projeto — comportamento da persistência da etapa 2, não alteração da spec de triagem.

## O que o agente 3 (trajetória profissional) entregou

| Arquivo | Conteúdo |
|---|---|
| `specs/sprint-2/trajetoria-profissional.md` | Quadro de escopo agora vs sprint posterior; botão **Avaliar trajetória**; mapeamento distinto; saída `AvaliacaoTrajetoria`; inelegível pode ser lido aqui sem reverter triagem; prompt próprio; informação insuficiente sem token; Given/When/Then e rastreabilidade |

Não editou contratos, ADRs, visão, legado, arquitetura, glossário, spec de triagem nem spec de avaliação de chatbot. Não implementou produto. Não habilitou o botão da primeira entrega. Não tornou resumo nem headline obrigatórios na importação da sprint 1. Não copiou taxonomia de `cargo_preprocessing`.

A ação `avaliar_trajetoria` **já tinha** onde pendurar: botão desabilitado no mapa (`specs/02-arquitetura.md`) e identificador em `PedidoTrajetoria`. Por isso este agente **não** registrou “arquitetura sem gancho” como bloqueio e **não** reescreveu a sprint 1 para antecipar módulo, endpoint ou campos.

## Conflitos entre specs

Se um agente posterior precisar mudar contrato, **não reescreve** o arquivo do outro: acrescenta entrada aqui com conflito, impacto e mudança proposta.

### 2026-09-22 — `candidatoId`: UUID (orquestrador) vs linha+hash (prompt da etapa 1)

**Conflito.** `specs/03-contratos-compartilhados.md` e ADR 003 definem `candidatoId` como UUID gerado na importação; `linhaOrigem` é metadado, não identidade de negócio. O prompt `prompts/sdd/01-agente-triagem-deterministica.md` manda, na ausência de CSV de amostra, usar o número da linha no arquivo mais um hash do conteúdo da linha; nome mapeado é opcional e não é identificador.

**O que a spec da etapa 1 fez.** Não reescreveu o contrato. Assumiu a regra do prompt só nessa parte, marcada como pendência: `candidatoId` persistido como `{linhaOrigem}:{sha256hex}` do conteúdo da linha; `nomeExibicao` só rótulo.

**Impacto.** Implementador da etapa 1 que seguir a spec gera identificador determinístico, não UUID. A etapa 2, se seguir o contrato ao pé da letra, espera UUID. Reordenar linhas na reimportação muda o id composto; UUID aleatório não sobreviveria à reimportação de outro modo (o lote é substituído).

**Mudança proposta ao orquestrador.** Manter o campo `candidatoId` no contrato. Escolher uma: (a) aceitar o id composto da etapa 1 e atualizar o contrato; ou (b) voltar ao UUID como chave e acrescentar `hashLinha` + `linhaOrigem` como fingerprint de reimportação. Até lá, a pendência da spec de triagem prevalece na parte em conflito.

**O que a spec da etapa 2 fez.** Não reescreveu o contrato nem a spec de triagem. Usa o `candidatoId` já persistido no lote no payload do LLM, no log de tokens e em `AvaliacaoIa`. Nome, se mapeado, permanece só no envelope local (ADR 007).

### 2026-09-22 — Extensão de `CriteriosQualitativos` (não é reescrita do contrato)

**Não é conflito de regra; é detalhe do dono.** O contrato descreve itens como identificador + enunciado. A spec da etapa 2 preenche enunciado como `nome` + `descricao` e acrescenta `ordem` e `eliminatorio`, este último para a regra: qualquer `nao_atende` impede `compativel`; `incompativel` se um critério marcado eliminatório for `nao_atende`, ou se todos os critérios informados forem `nao_atende`.

**Impacto.** Implementador que ler só o contrato não vê a flag. Quem implementar a etapa 2 deve seguir `specs/sprint-1/avaliacao-ia-chatbot.md`.

**Mudança proposta ao orquestrador (opcional).** Documentar `eliminatorio` e o par nome/descrição em `specs/03-contratos-compartilhados.md` quando o orquestrador revisar os tipos. Até lá, a spec da etapa 2 prevalece no conteúdo desses campos.

### 2026-09-22 — Etapa 3: inelegível no LLM de trajetória vs ADR 007 (escopo da etapa 2)

**Não é reescrita da ADR.** A ADR 007 e o diagrama de runtime proíbem mandar `inelegivel` ao LLM da **avaliação de chatbot**. Nenhuma ADR tratou de quem entra em `avaliar_trajetoria`. O prompt da etapa 3 manda escolher uma opção e recomenda permitir inelegível, porque a pergunta é outra.

**O que a spec da etapa 3 fez.** Adotou: qualquer candidato importado, inclusive inelegível. O resultado não reverte `DecisaoTriagem` e não libera token da etapa 2. Payload desta função: só `candidatoId` + perfil da vaga para trajetória + cargos/resumo/headline **mapeados para esta etapa**. Nome e planilha inteira continuam fora.

**Impacto.** Implementador da sprint 2 que seguir só a ADR 007 ao pé da letra bloquearia inelegível também neste botão. Quem implementar a etapa 3 deve seguir `specs/sprint-2/trajetoria-profissional.md` nesta parte. A etapa 2 permanece com o gate original.

**Mudança proposta ao orquestrador.** Na revisão da ADR 007 (ou da arquitetura), delimitar: inelegível não viaja na etapa 2; pode viajar na etapa 3 com payload mínimo próprio. Até lá, a spec da etapa 3 prevalece só para trajetória. Diagrama de runtime da sprint 1 **não** foi alterado: a seta única de LLM ali continua a da etapa 2.

### 2026-09-22 — Extensão de `PedidoTrajetoria` e tipos da etapa 3 (não é reescrita do contrato)

**Não é conflito de regra da primeira entrega; é detalhe do dono.** O contrato reserva `acao = avaliar_trajetoria` e `habilitada = false`. A spec da etapa 3 preenche, **para a sprint posterior**, `AvaliacaoTrajetoria`, `PromptTrajetoriaDoProjeto`, `PerfilVagaTrajetoria` e destinos `trajetoriaCargos[]` / `resumoProfissional` / `headline`. Rótulos de compatibilidade desta etapa: `aderente` | `parcialmente_aderente` | `distante` | `informacao_insuficiente` — não reutilizam `elegivel` / `inelegivel` nem `compativel` / `parcial` / `incompativel` (estes últimos o glossário reserva à etapa 2).

**Impacto.** Implementador da sprint 1 ignora esses tipos. Implementador da sprint 2 segue `specs/sprint-2/trajetoria-profissional.md`. O modelo de dados da sprint 1 **não** ganha migração de resumo/headline agora.

**Mudança proposta ao orquestrador (opcional).** Documentar os tipos e rótulos no contrato e no glossário quando a sprint 2 for puxada. Acrescentar módulo `trajetoria` no diagrama de módulos, reusando o adaptador da ADR 004, sem misturar o prompt da etapa 2. Até lá, este agente não reescreveu arquitetura nem contratos.

**O que a spec da etapa 3 fez com `candidatoId`.** Igual à etapa 2: usa o id já persistido no lote. Não reabre UUID vs linha+hash.

### 2026-09-23 — Revisão: job description, análise por pergunta, rankings

**Não reescreve** `specs/sprint-1/avaliacao-ia-chatbot.md`, os contratos nem as ADRs. Três specs novas prevalecem no disparo novo.

| Arquivo | Conteúdo |
|---|---|
| `specs/revisao/01-job-description.md` | Etapa depois dos critérios duros. Texto da vaga versionado. Variável `{{job_description}}` |
| `specs/revisao/02-analise-por-pergunta.md` | Sai a etapa de critérios qualitativos. A pergunta é o cabeçalho da coluna. Cruzamento com a resposta e com a job description |
| `specs/revisao/03-rankings.md` | Notas 0–100 técnica e comportamental (escrita). Final = média, meio para cima. Posição calculada no lote |

**Conflito com a etapa 2.** A spec de chatbot exige critérios qualitativos, `{{criterios_qualitativos}}`, flag `eliminatorio` e compatibilidade calculada (`compativel` / `parcial` / `incompativel`). A revisão tira essa etapa. O gate de quem chama o modelo permanece: só elegível com resposta utilizável.

**Conflito com o contrato.** `CriteriosQualitativos` deixa de ser obrigatório para disparar. `AvaliacaoIa` de disparo novo guarda notas e `por_pergunta` em vez da compatibilidade calculada. Avaliações já gravadas no schema antigo não ganham nota inventada.

**Conflito com duplicar projeto.** A etapa 1 copia só critérios duros. A spec 01 também copia a job description vigente.

**O que não muda.** Triagem determinística. Botão de trajetória desabilitado. Nome e critérios duros fora do prompt. Inelegível não vai ao LLM.

**Implementação.** As specs 01, 02 e 03 foram implementadas em seguida. A frase de espera acima vale só para o momento em que foi escrita.

### 2026-09-23 — Revisão: contains de cargo, bloqueio, empresa e idade com “anos”

**Não reescreve** `specs/sprint-1/triagem-deterministica.md`. Prevalece `specs/revisao/04-criterios-duros-cargo-empresa-idade.md`.

**Conflito.** A etapa 1 manda igualdade depois da normalização, sem `contains` e sem sinônimo no código. O código já tinha uma exceção: o aceito seguido de traço, barra ou pipe casa; `Assistente Comercial pleno` não casa. A revisão troca isso por palavras seguidas dentro do cargo, gênero mecânico e só três abreviações fixas: `Sr`, `Pl` e `Jr`. Não há tradução para o inglês. Escolaridade continua igualdade.

**O que entra.** Lista de cargos bloqueados (o bloqueio ganha do aceito). Critério de empresas bloqueadas, com coluna mapeada `empresa`. Idade lê `37 Anos`, `37 - Anos`, `37 Años` e `37 anos e 2 meses` como 37. Os meses não entram na conta.

**Sem IA.** Gênero e as abreviações `Sr`, `Pl` e `Jr` são automáticos. Inglês não entra sozinho. Cargo, empresa e idade continuam fora do prompt.

### 2026-09-24 — Revisão: justificativa da nota técnica e da nota comportamental

**Não reescreve** `specs/revisao/02-analise-por-pergunta.md` nem `specs/revisao/03-rankings.md`. Prevalece `specs/revisao/05-justificativa-das-notas.md` no disparo novo.

**Conflito.** A spec 02 exige exatamente as chaves `perfil`, `por_pergunta`, `trechos`, `nota_tecnica`, `nota_comportamental`. A spec 03 descreve o Excel com `Busca LKD` e sem resumo nem justificativa. O produto já exporta sem `Busca LKD`, com `Resumo` e com uma coluna `Justificativa pergunta N`. A spec 05 acrescenta `justificativa_nota_tecnica` e `justificativa_nota_comportamental`, obrigatórias no JSON novo, e fixa a ordem atual do Excel mais essas duas colunas.

**O que não muda.** Escala, média, posição e zeramento da nota técnica. `perfil` continua o resumo. Justificativa por pergunta continua. Avaliação já gravada não ganha texto inventado. Triagem dura e trajetória ficam fora.

## Correções do retrato prévio do orquestrador, feitas na spec de legado

O código confirmou o retrato geral. Pontos registrados com mais precisão em `specs/01-legado-e-gaps.md`:

- `escolaridade_preprocessing` mapeia `graduacao`/`gradu` para `pos-graduacao` (defeito vigente).
- Comentário “less than 10 times” vs corte real `<= 5`.
- `Cargo Anterior` não é coluna usada; só parâmetro default falso.
- `Nome` e `Justificativa` só em código comentado.
- Sem CSV local para descobrir colunas de resposta.
