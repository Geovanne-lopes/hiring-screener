# Sprint 2 — Trajetória profissional

Spec da etapa 3. Deixa a função especificada o bastante para não ser desenhada por acidente dentro da triagem nem da avaliação do chatbot, e para uma sprint futura implementá-la como botão separado. **Não implementa.** **Não puxa esta função para a primeira entrega.**

Dono: agente 3 (`prompts/sdd/03-agente-trajetoria-profissional.md`).

Contrato reservado: `PedidoTrajetoria` (`acao = avaliar_trajetoria`, `habilitada = false` na primeira entrega) em `specs/03-contratos-compartilhados.md`. Botão já no mapa de `specs/02-arquitetura.md`. Provedor: ADR 004. Payload: ADR 007, com o recorte desta etapa na secção 3 e a pendência em `specs/history.md`.

Fontes desta função: cargos da trajetória, resumo profissional e headline. **Não** são as respostas do chatbot. **Não** são os critérios duros de idade, cargo aceito e escolaridade.

---

## 1. Quadro de escopo

| Especificado agora | Implementar somente na sprint posterior |
|---|---|
| O botão **Avaliar trajetória** permanece no lugar que o orquestrador reservou: visível, desabilitado, texto de que a função vem em sprint posterior, **sem disparar modelo** e sem endpoint ativo | Habilitar o botão; criar o endpoint da ação `avaliar_trajetoria`; disparo explícito de lote |
| Importar, triar e avaliar chatbot **não** exigem coluna de trajetória, resumo nem headline | Destinos de mapeamento `trajetoriaCargos[]`, `resumoProfissional` e `headline`, distintos das colunas de chatbot |
| O modelo de dados da sprint 1 **não** é obrigado a persistir resumo nem headline; não há migração executável agora | Estender a persistência com os campos da secção 6 e gravar `AvaliacaoTrajetoria` |
| `PedidoTrajetoria.habilitada = false`; etapas 1 e 2 não leem este tipo para decidir nem para chamar LLM | `habilitada = true` só nesta função; pedido com `candidatoId` / `projetoId` |
| Esta spec descreve comportamento futuro e encaixe; a primeira entrega funciona sem ela | Prompt próprio, pré-visualização, chamada ao modelo, JSON de saída, tela de resultado desta etapa |
| Nenhuma chamada, nenhum prompt desta etapa e nenhum parser de currículo na sprint 1 | Cliente LLM desta etapa (mesmo adaptador da ADR 004, outro prompt); uma chamada por candidato |

Tudo o que for comportamento de produto desta função está na coluna da direita. A coluna da esquerda não autoriza gancho extra na sprint 1 além do botão já reservado.

---

## 2. Decisões fechadas nesta spec

| Tema | Decisão |
|---|---|
| Nome na UI | **Avaliar trajetória** (já reservado pelo orquestrador). Ação: `avaliar_trajetoria`. Não fundir com o botão de avaliar respostas do chatbot |
| Quem pode ser avaliado | **Qualquer candidato importado** do lote do projeto, inclusive `inelegivel` na triagem e inclusive quem ainda não tem `DecisaoTriagem`. Justificativa: secção 3 |
| O que o resultado **não** faz | Não reverte `DecisaoTriagem`. Não libera token da etapa 2. Não altera `AvaliacaoIa` |
| Fontes | Só colunas mapeadas para esta função: histórico de cargos, resumo, headline |
| Último cargo da etapa 1 | **Não** entra como histórico, a menos que o operador mapeie de novo, de forma explícita, a mesma coluna para `trajetoriaCargos[]` |
| Resumo e headline ambos vazios | `informacao_insuficiente`; **não chama** o modelo; não é `aderente` |
| Rótulos de compatibilidade | `aderente` \| `parcialmente_aderente` \| `distante` \| `informacao_insuficiente`. **Proibido** gravar `elegivel` / `inelegivel`. **Proibido** reutilizar `compativel` / `parcial` / `incompativel` da etapa 2 (glossário: esses três são só da avaliação do chatbot) |
| Tipo de saída | `AvaliacaoTrajetoria`, separado de `AvaliacaoIa` |
| Prompt | Artefato próprio por projeto, versionado como a etapa 2 (nova versão a cada save). **Não** copia o template de chatbot |
| Provedor | O da ADR 004. Esta spec não escolhe fornecedor. Uma HTTP por candidato |
| Parser de currículo | Fora. Sem PDF, sem `Atualização CV`, sem taxonomia de `cargo_preprocessing` |
| Sprint 1 | Intocada: sem campo obrigatório novo na importação, sem regra nova de cargo/idade/escolaridade |

---

## 3. Quem pode ser avaliado

Nenhuma ADR tratou desta pergunta **para a etapa 3**. A ADR 007 define o gate da **etapa 2** (inelegível não vai ao LLM da avaliação de chatbot). Esta spec **não reabre** esse gate.

**Opção adotada:** qualquer candidato importado, mesmo inelegível na triagem, porque a leitura da trajetória é outra pergunta.

**Opção rejeitada (não misturar):** somente elegíveis.

**Justificativa.** O operador pode querer entender o perfil de alguém recusado por idade ou escolaridade. Recusar a chamada nesta função só porque a etapa 1 falhou misturaria duas perguntas. O resultado **não** reverte a `DecisaoTriagem` e **não** libera token da etapa 2: inelegível continua invisível para o botão de avaliar chatbot. A tela deixa essa separação visível (secção 13.5).

Pendência de ADR: `specs/history.md`. Até o orquestrador revisar a ADR 007, esta spec prevalece **somente** para `avaliar_trajetoria`.

Quem **não** entra:

- linha que não é `CandidatoImportado` do lote corrente;
- candidato de outro projeto;
- desmarcado na lista desta execução (exclusão manual; não apaga triagem nem avaliação de chatbot).

Não é necessário ter resposta de chatbot utilizável. Não é necessário ter rodado a etapa 2.

---

## 4. O que a primeira entrega faz com isto

Somente:

1. Se o orquestrador reservou o botão, ele continua desabilitado, com o texto de sprint posterior, e **não** chama modelo.
2. Nenhuma chamada, nenhum prompt desta etapa e nenhuma coluna de trajetória são necessários para importar, triar ou avaliar chatbot.
3. O modelo de dados da sprint 1 **não** persiste `resumoProfissional` nem `headline` ainda. Os campos da secção 6 são extensão **futura**, sem migração executável agora.
4. Não há módulo `trajetoria` no diagrama da sprint 1. A ação já tem identificador e botão. O segundo caminho de LLM entra só quando esta sprint for implementada (pendência de arquitetura em `specs/history.md`). **Não** reescrever a spec da sprint 1 para “já ir implementando o gancho”.

Implementador da sprint 1: ignorar o restante deste arquivo como trabalho de código.

---

## 5. Encaixe na sprint posterior (sem reescrever a sprint 1)

Quando existir implementação:

- Novo módulo de backend `trajetoria`. Não mora em `triagem`. Não monta o prompt da etapa 2. **Reusa** o adaptador HTTP da ADR 004 (mesmo `LLM_BASE_URL`, chave, modelo, timeout, retry). O frontend **não** chama o provedor.
- A ação HTTP corresponde a `PedidoTrajetoria.acao = avaliar_trajetoria`.
- A seta de runtime desta função sai do botão **Avaliar trajetória**, não do botão de avaliar chatbot, e **não** exige `elegivel` nem resposta utilizável.
- Falha nesta função **não** apaga `DecisaoTriagem` nem `AvaliacaoIa`.

A arquitetura da sprint 1 continua verdadeira até essa implementação: a única seta de LLM descrita lá é a da etapa 2.

---

## 6. Extensão de dados (depois; sem migração agora)

Não alterar `specs/03-contratos-compartilhados.md` neste chat. Detalhe do dono de `PedidoTrajetoria`. Campos abaixo **não** existem na sprint 1.

### 6.1 Destinos novos no mapeamento (só sprint 2)

| Destino | Obrigatório para **importar** na sprint 1 | Obrigatório para **disparar** trajetória |
|---|---|---|
| `trajetoriaCargos[]` | não (nem existe) | sim: ao menos uma coluna mapeada de propósito |
| `resumoProfissional` | não | não; se ausente ou vazio **e** headline vazia → `informacao_insuficiente`, sem chamada |
| `headline` | não | não; mesma regra do resumo |

Cada item de `trajetoriaCargos[]`: `{ colunaMapeada, texto }`. Uma ou mais colunas. Texto da célula como veio, sem primeira palavra, sem lematização, sem dicionário comentado de `cargo_preprocessing`.

O operador **pode** mapear a mesma coluna já usada em `ultimoCargo`, de novo, para `trajetoriaCargos[]`. Isso é explícito. Sem esse segundo mapeamento, `ultimoCargo` **não** é enviado.

`Cargo Anterior` só entra se existir no arquivo **e** for mapeada para `trajetoriaCargos[]` de propósito (mesmo espírito da ADR 006).

Colunas de chatbot **não** entram neste payload, a menos que o operador tenha mapeado a **mesma** coluna também para um destino desta função. Nesse caso o texto aparece como cargo, resumo ou headline — não como “resposta de chatbot”.

### 6.2 `CandidatoImportado` (extensão futura)

Campos a acrescentar na sprint 2, todos opcionais na importação:

- `trajetoriaCargos`: lista; vazia se nada mapeado;
- `resumoProfissional`: string ou `null`;
- `headline`: string ou `null`.

A importação da sprint 1 permanece válida sem eles.

### 6.3 `PerfilVagaTrajetoria` (novo, por projeto)

Texto editável que descreve o que a vaga espera **da trajetória** (tipo de percurso, domínio, senioridade relatada nos cargos/resumo/headline). Distinto de `CriteriosDeterministicos` e de `CriteriosQualitativos`.

| Campo | Obrigatório para disparar |
|---|---|
| `projetoId` | sim |
| `versaoId` | sim quando gravado |
| `texto` | sim, não vazio após trim |
| `criadoEm` | sim |

Não injetar lista de cargos aceitos, faixa de idade nem escolaridade neste texto por sistema. Se a operação colar isso, aviso não silencioso no mesmo espírito da etapa 2: o modelo **não** reabre a porta de entrada. Idade, cargo aceito e escolaridade **não** entram no payload (secção 10).

Duplicar projeto (etapa 1) **não** copia este perfil nem o prompt de trajetória: o projeto novo começa vazio nestes artefatos.

### 6.4 `PromptTrajetoriaDoProjeto` (novo)

Mesmo modo **conceitual** da etapa 2: template editável, versão nova a cada save, avaliação presa à versão usada. **Outro** artefato. Editar este prompt **não** altera `PromptDoProjeto`. Editar o prompt de chatbot **não** altera este.

| Campo | Obrigatório para disparar |
|---|---|
| `promptTrajetoriaId` / `versao` | sim |
| `projetoId` | sim |
| `template` | sim |
| `perfilVagaTrajetoriaVersaoId` | sim nesta versão |
| `perfilVagaEmbutidoSnapshot` | sim |
| `criadoEm` | sim |

Se o perfil da vaga vigente divergir da versão embutida no prompt, o disparo bloqueia até a operação salvar o prompt de trajetória de novo.

### 6.5 `PedidoTrajetoria` (detalhe do dono, sprint 2)

```json
{
  "acao": "avaliar_trajetoria",
  "habilitada": true,
  "projetoId": "prj_01",
  "candidatoIds": ["12:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
  "promptTrajetoriaId": "prt_02"
}
```

Na primeira entrega este objeto não é executado; `habilitada` permanece `false` e `candidatoId` / `projetoId` não são obrigatórios (contrato).

### 6.6 `AvaliacaoTrajetoria` (saída, separada de `AvaliacaoIa`)

| Atributo | Obrigatório | Notas |
|---|---|---|
| `candidatoId` / `projetoId` | sim | o id **já persistido** no lote (pendência UUID herdada; secção 16) |
| `promptTrajetoriaId` | sim se houve chamada ou recusa alinhada a uma versão | |
| `perfilVagaTrajetoriaVersaoId` | sim se houve chamada | |
| `perfilTrajetoria` | sim se `sucesso` | ausente se insuficiente ou falha |
| `comparacaoComVaga` | sim se `sucesso` | |
| `compatibilidadeTrajetoria` | sim | um dos quatro rótulos da secção 2 |
| `trechos[]` | sim se `sucesso` | cada item cita fonte e trecho literal |
| `usoToken.entrada` / `saida` / `total` | se a API devolveu uso | senão registrar ausência, não inventar |
| `estado` | sim | `sucesso` \| `informacao_insuficiente` \| `falha_trajetoria` |
| `erro` | se falha | sem valor de chave, sem nome |

Nova execução **acrescenta** registro. Não reescreve o JSON anterior. Não reescreve `AvaliacaoIa`.

Reimportação do lote (já apaga `DecisaoTriagem` na etapa 1 e `AvaliacaoIa` na etapa 2): na sprint 2 também apaga `AvaliacaoTrajetoria` daquele `projetoId`. Isso é persistência desta etapa, não alteração da spec de triagem.

---

## 7. Pré-condições e avisos de coluna

### 7.1 Projeto sem mapeamento de cargos da trajetória

Recusa do disparo. **Não** completa a lista com `ultimoCargo`.

Mensagem:

> Não é possível avaliar a trajetória: mapeie ao menos uma coluna de cargos da trajetória. O último cargo da triagem não é usado como histórico, a menos que você mapeie essa coluna de novo aqui.

### 7.2 Arquivo sem resumo e/ou sem headline

Se o arquivo não tem a coluna, o operador não a mapeia. A função **avisa o que falta**, não inventa.

- Falta só resumo: aviso “Resumo profissional não mapeado.”
- Falta só headline: aviso “Headline não mapeada.”
- Faltam os dois: aviso “Nem resumo nem headline foram mapeados. Sem esses textos o modelo não será chamado; o resultado será informação insuficiente.”

O disparo **pode** seguir se `trajetoriaCargos[]` está mapeado: cada candidato sem resumo utilizável **e** sem headline utilizável sai `informacao_insuficiente` sem HTTP. Não é `aderente`.

### 7.3 Texto utilizável (resumo, headline, cargo)

Depois de converter para string, `strip` e colapsar whitespace Unicode para um único espaço, comprimento maior que zero.

Célula só com espaços → não utilizável.

### 7.4 Quando **não** chamar o modelo (padrão)

Por candidato, zero HTTP e `estado = informacao_insuficiente`, `compatibilidadeTrajetoria = informacao_insuficiente`, sem perfil inventado, quando resumo **e** headline estão ambos sem texto utilizável.

**Padrão: não chamar.** Chamar o modelo com carreira vazia autorizaria completar a trajetória. Esta spec não justifica exceção.

Cargos mapeados e preenchidos **não** bastam sozinhos para gastar token: sem resumo e sem headline o resultado continua informação insuficiente. Os cargos sozinhos, no legado, já alimentavam a triagem dura e a taxonomia — não são perfil desta função.

### 7.5 Quando chamar

Disparo explícito **e** candidato selecionado **e** `trajetoriaCargos[]` mapeado no projeto **e** (resumo utilizável **ou** headline utilizável) **e** perfil da vaga salvo **e** prompt de trajetória vigente alinhado **e** configuração LLM presente.

Uma chamada por candidato que passou nessa régua.

---

## 8. Prompt próprio

Não há segundo prompt escondido no código com regra de negócio que a tela não mostre. Instruções técnicas de formato aparecem na pré-visualização.

### 8.1 Delimitadores

| Delimitador | Conteúdo |
|---|---|
| `{{candidato_id}}` | `candidatoId` persistido |
| `{{perfil_vaga_trajetoria}}` | texto da versão embutida |
| `{{cargos_trajetoria}}` | pares `{ colunaMapeada, texto }` mapeados, inclusive vazios omitidos |
| `{{resumo_profissional}}` | texto mapeado, ou a linha `(ausente)` se não houver utilizável |
| `{{headline}}` | idem |

Proibido no template (validação ao salvar):

- placeholders `{{respostas_candidato}}`, `{{idade}}`, `{{cargo}}` (no sentido de último cargo da triagem), `{{escolaridade}}`, `{{nome}}`;
- pedir ao modelo que julgue idade, lista de cargos aceitos ou escolaridade como porta de entrada;
- pedir cadeia de raciocínio oculta;
- copiar o template da etapa 2.

Pré-visualização: cargos, resumo e headline interpolados. **Não** mostra o bloco de respostas do chatbot, a menos que a mesma coluna tenha sido mapeada para um destino desta função — e aí o texto aparece como cargo, resumo ou headline.

### 8.2 Template inicial recomendado

Versão 1 quando o projeto ainda não tem prompt de trajetória. Especificação, não código. **Não** é o template de chatbot.

Prefixo técnico visível:

```
INSTRUÇÕES TÉCNICAS DE FORMATO
Responda somente com um único objeto JSON válido.
Não use markdown, não use cerca de código, não escreva texto antes ou depois do JSON.
O objeto tem exatamente as chaves: perfilTrajetoria, comparacaoComVaga, compatibilidadeTrajetoria, trechos.
compatibilidadeTrajetoria é exatamente um de: aderente, parcialmente_aderente, distante.
trechos é uma lista de objetos com: fonte, colunaMapeada, trecho.
fonte é exatamente um de: resumo, headline, cargo.
colunaMapeada é o cabeçalho da coluna quando fonte é cargo; string vazia quando fonte é resumo ou headline.
Não invente chaves extras.
Não use os valores elegivel, inelegivel, compativel, parcial, incompativel.
```

Corpo editável:

```
Você descreve a trajetória profissional a partir somente dos cargos, do resumo e da headline delimitados abaixo.
Não leia respostas de chatbot.
Não julgue idade, lista de cargos aceitos da triagem nem escolaridade.
Não decida se a pessoa é elegível ou inelegível.
Não invente empregador, cargo, período, promoção, stack ou fato que não esteja nos textos delimitados.
Não complete a carreira quando resumo ou headline faltarem no trecho correspondente: omita o que não está escrito.
Não escreva cadeia de raciocínio.
Não escreva texto fora do JSON.

## Perfil esperado da vaga (trajetória)
{{perfil_vaga_trajetoria}}

## Identificador
{{candidato_id}}

## Cargos da trajetória
{{cargos_trajetoria}}

## Resumo profissional
{{resumo_profissional}}

## Headline
{{headline}}

## Tarefa
1. Em "perfilTrajetoria", um parágrafo curto (no máximo cinco frases) só com o que os campos acima sustentam.
2. Em "comparacaoComVaga", compare essa trajetória com o perfil esperado da vaga, sem reabrir a triagem dura.
3. Em "trechos", copie trechos literais de resumo, headline ou cargos que sustentam o julgamento. Cada trecho tem de aparecer nesses campos.
4. Em "compatibilidadeTrajetoria", use exatamente um de: aderente, parcialmente_aderente, distante.

Saída: somente o objeto JSON.
```

---

## 9. JSON de saída e validação

Contrato com o modelo: **um JSON único**. Planilha, markdown ou texto solto não são contrato.

### 9.1 Schema

```json
{
  "perfilTrajetoria": "string",
  "comparacaoComVaga": "string",
  "compatibilidadeTrajetoria": "aderente",
  "trechos": [
    {
      "fonte": "resumo",
      "colunaMapeada": "",
      "trecho": "string"
    }
  ]
}
```

`compatibilidadeTrajetoria` no JSON do modelo é só `aderente` | `parcialmente_aderente` | `distante`. `informacao_insuficiente` **não** é valor de modelo: é estado local, sem chamada.

### 9.2 Trechos

- lista não vazia em caso de `sucesso`;
- cada `trecho` não vazio é substring do texto enviado na fonte correspondente (`{{resumo_profissional}}`, `{{headline}}` ou o texto de `{{cargos_trajetoria}}` daquela `colunaMapeada`), após colapsar whitespace;
- trecho que não aparece → inválido (o modelo inventou);
- `perfilTrajetoria` e `comparacaoComVaga` obrigatórios, trim não vazio, no máximo 2000 caracteres cada;
- se existe trecho, `comparacaoComVaga` ou `perfilTrajetoria` (ao menos um dos dois) contém esse trecho após colapsar whitespace; senão `justificativa_sem_trecho` no sentido desta etapa (`falha_trajetoria`).

JSON com `elegivel`, `inelegivel`, `compativel`, `parcial` ou `incompativel` no campo de compatibilidade → inválido.

Falha: `estado = falha_trajetoria`, **sem** perfil inventado, **sem** apagar triagem nem `AvaliacaoIa`.

### 9.3 Exemplos (especificação)

Textos ilustrativos. Cabeçalhos não são nomes observados em CSV (não há arquivo local).

Enviado:

```
[coluna mapeada: (definida na importação para trajetória)]
Analista de dados sênior

Resumo: Atuação em painéis e qualidade de dados em varejo, com passagem por squads de BI.

Headline: Analista de dados | varejo
```

**A — `aderente` (JSON válido)**

```json
{
  "perfilTrajetoria": "A headline e o resumo descrevem atuação como analista de dados em varejo, com painéis e qualidade de dados: \"Atuação em painéis e qualidade de dados em varejo, com passagem por squads de BI.\"",
  "comparacaoComVaga": "O percurso em analista de dados no varejo sustenta o perfil pedido, com trecho \"Analista de dados | varejo\".",
  "compatibilidadeTrajetoria": "aderente",
  "trechos": [
    {
      "fonte": "resumo",
      "colunaMapeada": "",
      "trecho": "Atuação em painéis e qualidade de dados em varejo, com passagem por squads de BI."
    },
    {
      "fonte": "headline",
      "colunaMapeada": "",
      "trecho": "Analista de dados | varejo"
    },
    {
      "fonte": "cargo",
      "colunaMapeada": "(definida na importação para trajetória)",
      "trecho": "Analista de dados sênior"
    }
  ]
}
```

**B — `informacao_insuficiente` (sem JSON de modelo)**

Headline vazia, resumo vazio, cargos mapeados ou não. Zero HTTP. Persistir só o estado e o rótulo `informacao_insuficiente`. Sem `aderente`. Sem carreira inventada a partir do último cargo da triagem.

**C — inválida (não é distante, não é inelegível)**

Modelo devolve perfil que cita “dez anos como gestor em outra rede” e trecho ausente dos campos enviados. Após um reparo igualmente inválido: `falha_trajetoria`. `DecisaoTriagem` e `AvaliacaoIa` intactas.

---

## 10. Privacidade e payload

Não enviar a base inteira. Não enviar colunas **não** mapeadas para esta função. Não enviar nome (ADR 007). Logs com `candidatoId` e `projetoId`, sem nome e sem `LLM_API_KEY`.

Por candidato, e só isso:

- `candidatoId`;
- perfil da vaga para trajetória (versão embutida);
- textos de `trajetoriaCargos[]`, `resumoProfissional` e `headline` **mapeados e**, para resumo/headline, utilizáveis (ausência explícita como `(ausente)`, sem preencher com outro campo);
- o template da versão vigente.

Não entra:

- idade, escolaridade, cidade, equipe, status legado, justificativa interna, nome;
- `ultimoCargo` se a coluna não foi remapada para trajetória;
- `respostasChatbot[]` como bloco, salvo coincidência de coluna mapeada nesta função;
- candidatos de outros projetos;
- vários candidatos no mesmo HTTP;
- a planilha original completa.

Inelegível **pode** viajar **nesta** função, com o payload mínimo acima. Continua **proibido** na etapa 2.

---

## 11. Provedor, token e falha

Seguir ADR 004. Não escolher outro fornecedor. Variáveis e valores de exemplo: os mesmos da spec da etapa 2 / ADR 004. Chave real jamais nesta spec.

| Situação | Comportamento |
|---|---|
| Timeout, rede, 429/5xx | Retry limitado (`LLM_MAX_RETRIES`), backoff 1s depois 2s, **daquele** candidato |
| JSON inválido | Uma chamada de reparo com o JSON rejeitado + “Corrija para o schema exigido. Não invente fatos fora dos cargos, resumo e headline originais.” Depois: `falha_trajetoria` / `json_invalido` |
| `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` vazios | Lote recusado **antes** de HTTP; tela explica falta de configuração, sem mostrar a chave |
| Falha nesta função | Não apaga triagem nem avaliação de chatbot |

Registro de chamada: o mesmo espírito da etapa 2 (`candidatoId`, modelo, tokens se houver, status, tentativas, reparo), campo extra `acao = avaliar_trajetoria` para não misturar o custo no log da etapa 2.

Confirmação antes do token: mostrar N = quantos serão **enviados** (selecionados com resumo ou headline utilizável). Texto:

> Esta execução envia N candidato(s) ao modelo para avaliar trajetória, um por chamada. Quem está desmarcado ou sem resumo e sem headline não será enviado. O resultado não altera a triagem nem a avaliação do chatbot.

Se N = 0: ainda assim pode gravar `informacao_insuficiente` nos selecionados que falharam a régua da secção 7.4, **sem** HTTP. Se não houver ninguém selecionado, recusar.

---

## 12. Critérios de aceite

Não são testes automatizados.

### 12.1 Sprint 1 não quebra

#### CA-S1-01 — Triagem e chatbot sem headline/resumo

Given a primeira entrega implementada conforme `specs/sprint-1/triagem-deterministica.md` e `specs/sprint-1/avaliacao-ia-chatbot.md`  
When o operador importa, tria e avalia chatbot  
Then nenhuma leitura de headline ou resumo é exigida  
And a importação não recusa arquivo por falta desses campos

#### CA-S1-02 — Botão desabilitado não chama modelo desta etapa

Given o botão **Avaliar trajetória** na primeira entrega (reservado pelo orquestrador)  
When o operador o aciona (foco, clique ou atalho)  
Then nenhuma chamada de LLM desta etapa ocorre  
And não há request `avaliar_trajetoria`

### 12.2 Sprint posterior

#### CA-01 — Perfil só com trechos dos campos mapeados

Given um candidato com resumo e cargos mapeados para esta função  
When a avaliação de trajetória roda com sucesso  
Then `perfilTrajetoria` é persistido  
And cada item de `trechos` está presente nesses campos enviados  
And o perfil não cita fato que só existiria em coluna não mapeada

#### CA-02 — Inelegível por idade permanece inelegível

Given um candidato inelegível por idade  
When a trajetória é avaliada  
Then `DecisaoTriagem.resultado` permanece `inelegivel`  
And os motivos de idade permanecem  
And a tela mostra o resultado de trajetória **separado**, com o aviso de que não reverte a triagem e não libera a etapa 2

#### CA-03 — Prompt de trajetória não altera o de chatbot

Given um projeto com prompt de chatbot já salvo (`PromptDoProjeto`)  
When o operador edita o prompt de trajetória e salva  
Then o template e a versão vigente do prompt de chatbot não mudam

#### CA-04 — Headline e resumo vazios: insuficiente, zero token

Given headline vazia e resumo vazio nesse candidato  
When a função roda  
Then `compatibilidadeTrajetoria = informacao_insuficiente`  
And `estado = informacao_insuficiente`  
And nenhum token precisa ser gasto (zero HTTP para esse `candidatoId`)  
And o resultado não é `aderente`

#### CA-05 — Último cargo da triagem não vaza para o histórico

Given um último cargo usado na triagem  
And a coluna de trajetória **não** foi mapeada  
When a avaliação de trajetória é disparada ou o payload é montado  
Then esse cargo **não** é enviado como histórico profissional  
And a mensagem da secção 7.1 aparece se o disparo for recusado por falta de mapeamento

#### CA-06 — Botão distinto do chatbot

Given a navegação da sprint posterior  
When o operador avalia respostas do chatbot  
Then essa ação não dispara `avaliar_trajetoria`  
And o botão **Avaliar trajetória** é outra ação, habilitada só nesta sprint, com o próprio lote e o próprio prompt

#### CA-07 — Falha não apaga etapa 1 nem 2

Given `DecisaoTriagem` e `AvaliacaoIa` já persistidas  
When o provedor esgota retries ou o JSON de trajetória é inválido após reparo  
Then triagem e avaliação de chatbot permanecem iguais  
And o envelope desta etapa é `falha_trajetoria`

#### CA-08 — Pré-visualização sem bloco de chatbot

Given colunas de chatbot mapeadas para a etapa 2 e colunas distintas mapeadas para trajetória  
When o operador abre a pré-visualização desta função  
Then o texto contém cargos, resumo e/ou headline interpolados  
And não contém o bloco de respostas do chatbot

#### CA-09 — Mesma coluna nos dois lugares

Given o operador mapeou a **mesma** coluna para um destino de trajetória e para `respostasChatbot[]`  
When a pré-visualização de trajetória é montada  
Then esse texto pode aparecer como cargo, resumo ou headline  
And não é rotulado como resposta de chatbot nesta tela

#### CA-10 — Uma chamada por candidato; payload mínimo

Given dois importados selecionados, ambos com resumo utilizável  
When o lote de trajetória termina  
Then houve HTTP separado para cada um  
And nenhum payload contém a planilha inteira nem coluna não mapeada para esta função

#### CA-11 — Sem configuração LLM

Given `LLM_API_KEY` vazia  
When a trajetória é disparada para quem teria chamada  
Then não há HTTP  
And a tela explica a falta de configuração sem mostrar a chave

#### CA-12 — Exclusão manual

Given um importado desmarcado na lista desta execução  
When o operador confirma  
Then não há chamada para esse `candidatoId`  
And `DecisaoTriagem` não muda

---

## 13. Telas (somente sprint posterior)

Forma: aplicação web local (ADR 001). Sem login. Sem projeto corrente: “Abra ou crie um projeto para continuar.”

Na sprint 1 estas telas **não** são construídas. O mapa só mostra o botão desabilitado.

### 13.1 Mapeamento extra

Na importação da sprint 2, destinos adicionais da secção 6.1, claramente separados do bloco de chatbot e do bloco de triagem. Confirmar mapeamento de trajetória é explícito. Sugerir `Cargo` para trajetória **não** substitui o mapeamento de `ultimoCargo` da etapa 1; são dois destinos.

### 13.2 Perfil da vaga (trajetória) e prompt

Duas telas ou duas abas, **outras** que as da etapa 2: texto do perfil esperado da trajetória; editor do prompt de trajetória; lista de versões; pré-visualização de **um** candidato.

Não dispara LLM.

### 13.3 Lista do lote

Todos os importados. Selecionáveis por padrão. Inelegíveis **selecionáveis aqui** (diferente da etapa 2). Coluna de triagem visível (elegível / inelegível / ainda sem decisão). Aviso persistente:

> Avaliar trajetória não muda a triagem e não autoriza avaliar o chatbot.

Barra: **Revisar e avaliar trajetória**. Só habilita com mapeamento de cargos desta função, perfil da vaga, prompt alinhado. Senão explica o que falta.

### 13.4 Confirmação

N, lista resumida, modelo configurado sem chave, texto da secção 11. **Confirmar envio** / **Voltar**. Fechar sem confirmar → zero chamada.

### 13.5 Resultado

Por candidato, **ao lado** (não no lugar) do envelope da sprint 1:

| Estado desta etapa | O que mostra |
|---|---|
| não executada | “Trajetória não avaliada” |
| `informacao_insuficiente` | “Informação insuficiente” — falta resumo e headline; **não** usar cor de “aderente” |
| `sucesso` | perfil; comparação com a vaga; rótulo `aderente` / `parcialmente aderente` / `distante`; trechos com fonte; versão do prompt de trajetória; tokens se houver |
| `falha_trajetoria` | “Falha na trajetória”, distinto de `distante` e de `inelegivel`; ação avaliar de novo |

Se a triagem é `inelegivel`, os motivos da etapa 1 continuam o resultado principal da porta de entrada. A trajetória é bloco secundário, com o aviso da secção 13.3.

Filtro desta etapa: todos / insuficiente / aderente / parcialmente aderente / distante / falha — **sem** reutilizar os filtros `elegível` / `inelegível` como se fossem deste julgamento.

---

## 14. Erros

| Situação | Comportamento |
|---|---|
| Sem projeto | “Abra ou crie um projeto para continuar.” |
| Sem mapeamento de `trajetoriaCargos[]` | Recusa. Mensagem da secção 7.1 |
| Perfil da vaga vazio | “Cadastre o perfil da vaga para trajetória antes de avaliar.” |
| Sem prompt de trajetória vigente | “Salve um prompt de trajetória antes de avaliar.” |
| Perfil e prompt desalinhados | Salvar o prompt de trajetória de novo |
| Ninguém selecionado | Recusa |
| Config LLM vazia | Recusa do que seria HTTP; mensagem sem chave |
| JSON inválido após reparo | `falha_trajetoria`, `json_invalido` |
| Trecho fora das fontes | `falha_trajetoria`, `trecho_nao_encontrado` |
| Botão na sprint 1 | Desabilitado; zero request |

---

## 15. Rastreabilidade

Requisito futuro → entrada mapeada → botão → JSON de saída → o que explicitamente **não** altera na sprint 1 → critério de aceite.

| ID | Requisito futuro | Entrada mapeada | Botão | JSON / persistido | Não altera na sprint 1 | Aceite |
|---|---|---|---|---|---|---|
| R1 | Perfil a partir da trajetória | `trajetoriaCargos[]`, `resumoProfissional`, `headline` | **Avaliar trajetória** | `perfilTrajetoria`, `trechos` | Importação sem esses campos; triagem sem os ler | CA-01, CA-S1-01 |
| R2 | Comparar com a vaga | `PerfilVagaTrajetoria` + fontes | idem | `comparacaoComVaga` | `CriteriosDeterministicos` e `CriteriosQualitativos` intactos | CA-01 |
| R3 | Compatibilidade da trajetória com rótulos próprios | fontes desta etapa | idem | `aderente` / `parcialmente_aderente` / `distante` / `informacao_insuficiente` | Não grava `elegivel` / `inelegivel`; não reusa rótulos da etapa 2 | CA-02, CA-04 |
| R4 | Trechos que sustentam | resumo, headline, cargos mapeados | idem | `trechos[]` | Não lê chatbot por default | CA-01, CA-08 |
| R5 | Sem inventar carreira | resumo e headline | idem; **sem** HTTP se ambos vazios | `informacao_insuficiente` | — | CA-04 |
| R6 | Não usar último cargo da triagem por omissão | só `trajetoriaCargos[]` explícito | recusa se faltar | payload sem `ultimoCargo` implícito | ADR 006 e etapa 1 intactas | CA-05 |
| R7 | Inelegível pode ser lido; triagem permanece | lote importado | habilitado só na sprint 2 | `AvaliacaoTrajetoria` + `DecisaoTriagem` inalterada | Gate da etapa 2 (ADR 007) intacto | CA-02 |
| R8 | Prompt próprio versionado | — | editor desta etapa | `PromptTrajetoriaDoProjeto` | `PromptDoProjeto` não muda | CA-03 |
| R9 | Mesmo provedor, uma chamada, token, JSON inválido | payload mínimo | confirmação N | registro `acao = avaliar_trajetoria` | Cliente da etapa 2 / regras duras intactos | CA-07, CA-10, CA-11 |
| R10 | Botão separado; sprint 1 desabilitada | — | reservado, depois habilitado | `PedidoTrajetoria` | Specs sprint 1 e botão morto | CA-S1-02, CA-06 |
| R11 | Privacidade | só colunas desta função | — | sem base inteira, sem nome | ADR 007 nome/planilha | CA-10, CA-08 |
| R12 | Falha isolada | — | avaliar de novo | `falha_trajetoria` | `AvaliacaoIa` e triagem | CA-07 |

Validação e erro: secções 7, 9, 11 e 14. Given/When/Then: secção 12.

---

## 16. Pendências (sem reescrever contrato nem sprint 1)

### 16.1 `candidatoId`

Herdado: contrato/ADR 003 pedem UUID; spec da etapa 1 usa `{linhaOrigem}:{sha256hex}`. Esta spec usa o id **já persistido**, como a etapa 2. Não reabre a disputa.

### 16.2 Módulo e segundo caminho de LLM

A ação `avaliar_trajetoria` **tem** onde pendurar: botão no mapa e identificador no contrato. **Não** há módulo `trajetoria` nem seta de LLM desta etapa no diagrama de runtime da sprint 1 — de propósito, a primeira entrega não a executa. Proposta ao orquestrador: quando a sprint 2 for puxada, acrescentar o módulo e a seta **sem** alterar o gate da etapa 2. Registrado em `specs/history.md`. Esta spec **não** reescreve `specs/02-arquitetura.md`.

### 16.3 ADR 007 e inelegível

A ADR 007 proíbe inelegível no LLM da etapa 2. Esta etapa adota o contrário **no próprio botão**, com payload mínimo distinto. Proposta: parágrafo na ADR 007 delimitando o escopo. Até lá, esta spec prevalece só para trajetória.

### 16.4 Tipos novos

`AvaliacaoTrajetoria`, `PromptTrajetoriaDoProjeto`, `PerfilVagaTrajetoria` e os três destinos de mapeamento são detalhe do dono. Proposta opcional: documentá-los no contrato compartilhado quando o orquestrador revisar os tipos. Até lá, este arquivo prevalece no conteúdo.

---

## 17. Fora desta spec

- Implementar o botão funcional, o parser de currículo, o cliente de LLM, tela, `.env` real, migração
- Fundir esta avaliação com a das respostas do chatbot
- Alterar regras de cargo, idade e escolaridade
- Tornar resumo ou headline obrigatórios na importação da primeira entrega
- Copiar taxonomias comentadas de `cargo_preprocessing` como perfil profissional
- Reescrever specs da sprint 1, ADRs, arquitetura, contratos ou glossário
- Fine-tuning, embedding, RAG, segundo fornecedor
- Autenticação, JWT, papéis
- Funil Excel (ADR 005)

## 18. Definition of done da spec

- [x] Quadro de escopo nas duas colunas, com produto da função na sprint posterior
- [x] Botão próprio nomeado; entradas mapeadas distintas; não inventar a partir do último cargo da triagem
- [x] Saída separada de `AvaliacaoIa`, rótulos que não reutilizam `elegivel` / `inelegivel`
- [x] Inelegível pode ser avaliado aqui, sem reverter triagem nem liberar etapa 2
- [x] Prompt próprio versionado, template distinto, pré-visualização sem chatbot por default
- [x] Mesmo mecanismo da ADR 004; uma chamada; falha isolada; privacidade de colunas
- [x] Informação insuficiente sem chamada quando resumo e headline vazios
- [x] Sprint 1: botão desabilitado, sem campos obrigatórios novos, sem migração
- [x] Given/When/Then da sprint posterior + bloco “Sprint 1 não quebra”
- [x] Rastreabilidade no formato pedido
- [x] Pendências só em `specs/history.md` e na secção 16; contratos e sprint 1 intocados
- [x] Sem implementação de produto
