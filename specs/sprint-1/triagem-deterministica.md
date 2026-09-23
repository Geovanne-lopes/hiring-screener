# Sprint 1 — Triagem determinística

Spec da etapa 1. Permite a um agente implementador construir só esta etapa, com a avaliação por IA ainda desligada, e o resultado já utilizável: inelegível com motivos, ou elegível na triagem.

Esta etapa não chama LLM, não estima token e não escreve template de prompt. O botão **Avaliar trajetória** permanece no lugar que o orquestrador reservou: visível, desabilitado, texto de sprint posterior, sem disparar modelo. Esta spec não detalha esse botão além de respeitar esse lugar.

Dono: agente 1 (`prompts/sdd/01-agente-triagem-deterministica.md`).

Contratos: `CriteriosDeterministicos`, `CandidatoImportado`, `DecisaoTriagem` em `specs/03-contratos-compartilhados.md`. Stack: módulo `triagem` no backend, sem HTTP externo (ADR 002).

---

## 1. Decisões fechadas nesta spec

| Tema | Decisão |
|---|---|
| Faixa de idade | Inclusiva nos dois extremos: `minima ≤ idade ≤ maxima` |
| Escolaridade | Lista de valores aceitos configurada pelo operador (mesmo padrão dos cargos). Não é nível mínimo. Não é o agrupamento do legado |
| Normalização | Só mecânica e visível: trim, colapso de espaços internos, minúsculas, sem acento. Sem sinônimo, sem primeira palavra, sem `gestor`→`gerente` |
| Identificador | `candidatoId` = `{linhaOrigem}:{sha256hex}` do conteúdo da linha. Nome, se mapeado, é rótulo. **Pendência:** ver secção 12 e `specs/history.md` |
| Reimportação | Substitui o lote atual do projeto e apaga as `DecisaoTriagem` daquele projeto. Nova execução é obrigatória |
| Funil Excel | Fora desta entrega (ADR 005). Sem gancho de funil |
| Cidade | Não é critério duro desta etapa |

### 1.1 Modelo de escolaridade (completo)

O operador configura uma **lista de valores aceitos**, cada item um texto, com o bloco ativo ou inativo.

Comparação: o texto mapeado da célula passa pela normalização mecânica da secção 5; cada item da lista passa pela mesma normalização; há aceite se o valor comparado for **igual** a algum item comparado da lista. Não há `str.contains`, não há recorte antes de ` · `, não há dicionário `bacharelado`/`pos-graduacao`, não há colapso de valor raro para `bacharelado`.

Este modelo é o preferido pelo prompt da etapa 1. Nenhuma ADR escolheu outro. Não foi rejeitado.

Justificativa de não usar nível mínimo: o legado agrupava por substring e rebaixava raro a `bacharelado`; um “mínimo na escada” exigiria catalogar todos os níveis e equivalências, o que reintroduz taxonomia no código. A lista editável devolve o controle à operação: se quiser aceitar “Bacharelado · Estatística” e “Bacharelado”, inclui os dois textos.

---

## 2. Projeto e tela

Forma: aplicação web local (ADR 001). Sem login.

### 2.1 Criar, abrir, editar, reutilizar

| Ação | Comportamento |
|---|---|
| Criar | Operador informa `nome` (obrigatório, não vazio após trim). Sistema gera `projetoId`, timestamps, e `CriteriosDeterministicos` inicial: os três blocos **inativos**, listas vazias, idade sem mínima/máxima |
| Abrir | Lista de projetos persistidos (nome, datas). Abrir um torna-o o projeto corrente da sessão |
| Editar | Só o `nome` do projeto corrente. Critérios duros têm tela própria (secção 2.2) |
| Reutilizar | Duplicar o projeto corrente: novo `projetoId`, novo nome (operador informa), **cópia** dos critérios duros vigentes. Sem copiar candidatos, mapeamento, decisões. Serve para outra vaga com a mesma regra dura |

Sem projeto corrente, as telas de critérios, importação, execução e resultado não operam. Ver secção 9.

Persistência: SQLite (ADR 003). Fechar e reabrir o programa mantém projetos, critérios, lote importado e decisões.

### 2.2 Tela dos critérios duros

Três blocos independentes, nesta ordem: **Cargos aceitos**, **Faixa de idade**, **Escolaridade**. Cada bloco tem interruptor **ativo / inativo**.

O interruptor inativo não apaga a configuração já preenchida; só deixa de aplicá-la na próxima execução.

#### Bloco cargos aceitos

- Lista editável na tela: incluir, remover, revisar. **Não mora no código-fonte.** Não copiar `status_dentro`, `status_fora`, nem o dicionário `to_lemmantise` do legado.
- Campo de inclusão: texto livre; ao confirmar, aplica-se a regra de lista da secção 9 (vazio ignorado, duplicata recusada, aviso).
- Cada item visível como o operador digitou (valor original da lista). A forma comparada aparece ao lado, em texto secundário, para a normalização não ser invisível.

#### Bloco faixa de idade

- `idade mínima` e `idade máxima`: inteiros.
- Texto fixo na tela (não é opção): “Os limites são inclusivos: a idade mínima e a máxima também são aceitas.”
- Não há faixas `Ate 18` / `19 a 24` nem `pd.cut`.

#### Bloco escolaridade

- Lista editável de valores aceitos, igual em comportamento ao bloco de cargos (incluir, remover, revisar, original + forma comparada).
- Texto fixo: “A célula da planilha precisa coincidir com um item desta lista, depois da normalização visível. Valores raros não são reclassificados.”

#### Barra da tela

- **Salvar critérios**: persiste o vigente e gera novo `criteriosVersao` (identificador novo a cada gravação bem-sucedida, mesmo que o conteúdo seja igual — a execução aponta para a versão usada).
- Aviso persistente, não bloqueante no rascunho: se um bloco está ativo e ainda vazio/incompleto, a tela diz qual critério falta. A **execução** é que bloqueia (secção 7).
- Não há botão de disparar LLM nesta tela.

---

## 3. Importação

### 3.1 Arquivo e encoding

Formatos: CSV e XLSX (arquitetura).

CSV:

- Encoding selecionável, no mínimo `latin-1` e `utf-8`.
- Padrão: `latin-1`, porque o legado lia `pd.read_csv(..., encoding='latin-1')`.
- **UTF-8 escolhido e o arquivo é UTF-8 válido:** a importação lê com os caracteres corretos; não há conversão para latin-1.
- **UTF-8 escolhido e a decodificação falha:** a importação é recusada, com mensagem de que o arquivo não é UTF-8 válido e que o operador pode tentar `latin-1` (caso típico do mapeamento legado).
- **latin-1 escolhido:** a leitura não falha por byte inválido (latin-1 decodifica qualquer byte). Se o arquivo era UTF-8, a pré-visualização das primeiras linhas mostra o texto distorcido; o operador troca o encoding e reimporta. Não há recodificação silenciosa.

XLSX: encoding da tela fica desabilitado (o formato já traz Unicode). Leitura via openpyxl/pandas, como na arquitetura.

Pré-visualização obrigatória antes de confirmar a importação: nomes das colunas e até 5 primeiras linhas, já decodificadas com o encoding escolhido.

### 3.2 Mapeamento de colunas

O operador mapeia colunas do arquivo para os campos de `CandidatoImportado` usados nesta etapa.

| Destino | Obrigatório para importar | Obrigatório para **executar** a triagem |
|---|---|---|
| Último cargo → `ultimoCargo` | não | sim, se critério de cargo **ativo** |
| Idade → `idade` | não | sim, se critério de idade **ativo** |
| Escolaridade → `escolaridade` | não | sim, se critério de escolaridade **ativo** |
| Nome → `nomeExibicao` | não | não |
| Respostas de chatbot → `respostasChatbot[]` | não | não |
| Cidade / status legado | não | não |

Regras:

- Se existir no arquivo uma coluna chamada `Cargo` (após strip do nome) e o operador ainda não escolheu outra para último cargo, essa coluna vem **sugerida**. O operador confirma. A importação não segue sem essa confirmação explícita (botão confirmar mapeamento).
- Não sugerir `Cargo Anterior`. Só entra se existir no arquivo **e** o operador a mapear de propósito (ADR 006).
- Não inventar coluna `Nome`. Se o arquivo tiver alguma coluna que o operador identifique como nome, ele mapeia; `nomeExibicao` é **rótulo**, não identificador.
- Colunas de resposta de chatbot: sem nome prescrito. Se o operador mapear uma ou mais, o texto é **guardado** no candidato, sem julgamento nesta etapa, para a etapa 2 usar.
- `Atualização CV` não é campo desta triagem.

### 3.3 Identificador estável

Não há CSV de amostra no repositório. Coluna `Nome` não está confirmada no código vigente.

- `nomeExibicao`, se mapeado, é só rótulo na tela de resultado.
- `linhaOrigem`: índice da linha de candidato no arquivo, 1-based após o cabeçalho (a primeira linha de dados é `1`). Metadado de rastreio.
- `candidatoId`: string `{linhaOrigem}:{sha256hex}`, onde o hash é SHA-256 hexadecimal (64 caracteres) de, em UTF-8: as células da linha **na ordem das colunas do arquivo**, valores como texto já decodificado, separados por U+001F. Célula vazia entra como string vazia. Não usar UUID.

**Pendência (não reescreve o contrato):** o orquestrador definiu `candidatoId` como UUID. Esta etapa assume a regra deste prompt. Ver secção 12.

A etapa 2 referencia a mesma pessoa por esse `candidatoId` persistido no lote.

### 3.4 Persistência do lote

Confirmar importação:

1. Grava `mapeamentoColunas` no projeto.
2. Substitui `CandidatoImportado[]` do projeto (lote anterior apagado).
3. Apaga `DecisaoTriagem[]` daquele projeto (o lote mudou).
4. Não dispara triagem sozinha.

Cada `CandidatoImportado` guarda os valores **originais** mapeados (`ultimoCargo`, `idade`, `escolaridade` como vieram da célula, sem `pd.cut`, sem primeira palavra, sem virar `bacharelado`). Também guarda `respostasChatbot` se mapeadas, sem classificá-las.

Linhas totalmente vazias no arquivo são ignoradas na importação (não viram candidato). Se, depois disso, não restar nenhuma linha de candidato, a importação é recusada (secção 9).

---

## 4. Normalização visível

Única normalização desta etapa, aplicada a **último cargo**, **escolaridade** e aos itens das listas aceitas:

1. Converter para string.
2. `strip` nas pontas.
3. Colapsar qualquer sequência de whitespace Unicode para um único espaço U+0020.
4. Decompor NFKD e remover marcas combinantes (acento some).
5. Minúsculas (case fold de Unicode, equivalente prático: `casefold`).

O valor original **não é substituído** na persistência. A forma comparada é derivada na execução e **exibida** no resultado (lido → comparado).

Proibido, inclusive como “atalho” interno:

- ficar só com a primeira palavra (`just_first_split=True` do legado)
- pontuação → espaço + stop words + lematização + tradução do legado
- `vendedora`→`vendedor`, `externa`→`externo`, `gestor`→`gerente`, `gns`→`gestor`
- agrupar escolaridade por substring; `'graduacao'`/`'gradu'` → `pos-graduacao`
- categorias com poucas ocorrências → `bacharelado`
- lista de sinônimos comentada (“CARREFOUR STAND”) como regra escondida

Sinônimo desejado pela operação entra como **mais um item na lista editável**, não como dicionário no código.

A tela de critérios mostra, sob as listas, a frase: “A comparação ignora maiúsculas, acentos e espaços extras. Não reduz o cargo à primeira palavra e não aplica sinônimos automáticos.” Sem essa exibição, a normalização seria invisível e fora desta spec.

---

## 5. Avaliação de um candidato

Módulo `triagem`: função pura sobre (`CandidatoImportado`, `CriteriosDeterministicos` da versão em execução). Zero HTTP.

Ordem de avaliação na lista de motivos: cargo, idade, escolaridade. A ordem **não muda o conjunto**: todos os critérios **ativos** são avaliados; todas as falhas entram em `motivos`. Não parar na primeira.

### 5.1 Decisão

- `elegivel` somente se todos os critérios ativos passaram.
- `inelegivel` se qualquer critério ativo falhou (incluindo dado obrigatório ausente ou inválido daquele critério).
- `motivos` vazia se elegível.
- `criteriosInativos`: nomes dos critérios inativos nesta execução (`cargo`, `idade`, `escolaridade`). Na tela, cada um aparece como **não aplicado**. Critério inativo não elimina e não gera motivo.

Não existe `aguardando` em `DecisaoTriagem`. Aguardar resposta é composição posterior (contrato).

Não existe score, `contratado`, `status_dentro`, `Sim`/`Nao` do modelo, nem limiar 0,4.

### 5.2 Cargo (se ativo)

Dado inválido quando `ultimoCargo` está ausente, não é string, ou, após os passos 1–3 da normalização (strip + colapso de espaço), fica vazio. Motivo: `dado_obrigatorio_ausente_ou_invalido` no critério cargo. Não marcar elegível.

Caso contrário: se o valor comparado **não** é igual a nenhum item comparado da lista `cargos.aceitos`, motivo `cargo_fora_da_lista`. A mensagem cita o cargo **lido**, a forma **comparada** e a lista aceita **como o operador cadastrou** (originais da lista).

Se o valor comparado coincide com um item, o critério cargo passou.

### 5.3 Idade (se ativo)

A idade persistida é o valor original da célula, sem faixa.

Válida somente se, após trim, for um número inteiro em decimal (aceita `25` e `25.0` cujo valor seja inteiro), no intervalo `0 < idade ≤ 120`. Fora isso — vazio, `25 anos`, `N/A`, negativo, zero, não numérico, maior que 120 — motivo `dado_obrigatorio_ausente_ou_invalido` no critério idade. Não usar `pd.cut`.

Se válida:

- inelegível por idade se `idade < minima` **ou** `idade > maxima` (limites **inclusivos**: `idade == minima` e `idade == maxima` passam neste critério).
- Motivo `idade_fora_da_faixa`, citando a idade lida e a faixa configurada, e dizendo que os limites são inclusivos.

### 5.4 Escolaridade (se ativo)

Dado inválido quando a célula está ausente ou, após strip + colapso de espaço, fica vazia, ou o texto (sem depender de acento) é `#name?` (lixo de fórmula do Excel, visto no legado). Motivo `dado_obrigatorio_ausente_ou_invalido` no critério escolaridade.

Caso contrário: se o valor comparado não é igual a nenhum item comparado de `escolaridade.configuracao.aceitos`, motivo `escolaridade_fora_da_lista`, citando o texto lido, o comparado e a lista cadastrada.

Não reclassificar valor raro.

### 5.5 Forma de cada motivo

Cada item de `motivos`:

| Campo | Obrigatório | Conteúdo |
|---|---|---|
| `criterio` | sim | `cargo` \| `idade` \| `escolaridade` |
| `codigo` | sim | `cargo_fora_da_lista` \| `idade_fora_da_faixa` \| `escolaridade_fora_da_lista` \| `dado_obrigatorio_ausente_ou_invalido` |
| `valorLido` | sim | texto (ou representação) original da célula; `null` se ausente |
| `valorComparado` | sim se houve normalização aplicável | forma comparada; `null` se o dado era inválido antes de comparar |
| `esperado` | sim nos códigos de “fora da lista/faixa” | lista original de cargos/escolaridade, ou `{ minima, maxima }` |
| `mensagem` | sim | frase para a pessoa entender se foi cargo, idade, escolaridade ou dado inválido |

Candidato inelegível **não** é descrito na UI como entrada da avaliação por IA: sem badge “pronto para IA”, sem ação de avaliar habilitada nessa linha. O envelope de leitura (contrato) para esses casos é `resultadoExibicao: inelegivel` + `motivos`.

---

## 6. Execução do lote

Pré-condições (qualquer falha **bloqueia o lote inteiro**, ninguém é classificado, ninguém é aceito em silêncio):

1. Há projeto corrente.
2. Há lote de `CandidatoImportado` com pelo menos um candidato.
3. Mapeamento cobre os campos dos critérios **ativos**.
4. Nenhum critério ativo está com configuração vazia/incompleta (secção 7).
5. Se idade ativa: mínima e máxima presentes, inteiros, `minima ≤ maxima`, ambos em `1..120`.

Então o backend avalia cada candidato, persiste `DecisaoTriagem[]` com `criteriosVersao` da versão vigente no momento da execução, e devolve o lote. Nenhuma chamada externa.

Reexecutar substitui as decisões anteriores daquele projeto.

Três critérios inativos: a execução é permitida; todos saem `elegivel`, `motivos` vazias, `criteriosInativos` com os três nomes. Isso não é “lista vazia aceita todos”: lista vazia **ativa** bloqueia (secção 7).

---

## 7. Critério ativo e vazio

Lista vazia **não** significa aceitar todos.

Bloqueia a execução, com mensagem que diz **qual** critério falta:

| Critério ativo | Configuração incompleta |
|---|---|
| Cargo | `cargos.aceitos` sem nenhum item válido (depois de ignorar vazios) |
| Idade | `minima` ou `maxima` ausente |
| Escolaridade | `escolaridade.configuracao.aceitos` sem nenhum item válido |
| Idade | `minima > maxima` (erro próprio, secção 9) |

Mensagens (texto a usar):

- “Não é possível executar a triagem: o critério de cargos aceitos está ativo e a lista está vazia.”
- “Não é possível executar a triagem: o critério de idade está ativo e a faixa (mínima e máxima) não está preenchida.”
- “Não é possível executar a triagem: o critério de escolaridade está ativo e a lista de valores aceitos está vazia.”

Se vários faltarem, listar todos na mesma recusa (não só o primeiro).

---

## 8. Tela de resultado

Lista os candidatos do lote do projeto corrente.

Colunas mínimas:

- rótulo: `nomeExibicao` se mapeado; senão `candidatoId` (e `linhaOrigem` visível como apoio)
- decisão: `Elegível na triagem` ou `Inelegível` (glossário; nunca `contratado` / `fora do perfil` / `Dentro do Perfil`)
- motivos: mensagens; lista vazia mostra “—”
- critérios não aplicados: os de `criteriosInativos`, rótulo **Não aplicado**
- para cargo e escolaridade que passaram ou falharam por lista: valor lido e valor comparado

Filtro por decisão: todos / elegível / inelegível.

Candidato inelegível não aparece como fila da etapa 2. Elegível nesta entrega, com IA desligada, aparece como elegível na triagem — o envelope `elegivel_pendente_ia` / `aguardando_resposta` é composição do contrato, não dispara modelo aqui.

Exportar CSV/Excel **deste** resultado por candidato (id, decisão, motivos) é permitido como apoio (ADR 005). Não é o funil `Analise [RENOMEAR].xlsx`. Esta spec não exige o export na primeira fatia da etapa 1; a tela de lista + filtro já torna o resultado utilizável.

Botão **Avaliar trajetória**: visível no mapa de navegação, desabilitado, sem request.

---

## 9. Erros

| Situação | Comportamento |
|---|---|
| Não há projeto aberto | Qualquer ação de critérios, importar, executar ou ver resultado desta etapa é recusada. Mensagem: “Abra ou crie um projeto para continuar.” |
| Não há arquivo | Importar sem arquivo selecionado, ou arquivo inacessível: recusa. Mensagem: “Selecione um arquivo CSV ou XLSX para importar.” |
| Encoding UTF-8 inválido | Recusa da importação (secção 3.1) |
| Mapeamento incompleto para critério ativo | Execução recusada. Mensagem cita o campo: “Não é possível executar a triagem: o critério de {cargo/idade/escolaridade} está ativo e a coluna correspondente não foi mapeada.” |
| Faixa com mínima maior que máxima | Não executa. Mensagem: “Não é possível executar a triagem: a idade mínima é maior que a máxima.” Impedir também gravar essa faixa inválida no bloco de idade (validação na tela ao salvar) |
| Item vazio na lista de cargos ou de escolaridade | Ao incluir: ignorar, avisar “Item vazio ignorado.” Não gravar string vazia |
| Item duplicado (igualdade após a normalização da secção 4) | Não duplicar. Avisar “Este valor já está na lista.” Manter o item que já existia (texto original antigo) |
| Planilha sem linhas de candidato | Importação recusada. Mensagem: “O arquivo não contém linhas de candidato.” Não persistir lote vazio |
| Execução sem lote importado | Recusa. Mensagem: “Importe uma planilha antes de executar a triagem.” |
| Critério ativo vazio | Secção 7 |

---

## 10. Contratos desta etapa (detalhe do dono)

Não altera os arquivos do orquestrador. Preenche o que o contrato deixou para o agente 1.

### 10.1 `CriteriosDeterministicos` vigente

```json
{
  "cargos": {
    "ativo": true,
    "aceitos": ["Analista de dados", "Cientista de dados"]
  },
  "idade": {
    "ativo": true,
    "minima": 18,
    "maxima": 45
  },
  "escolaridade": {
    "ativo": true,
    "configuracao": {
      "modelo": "lista_valores_aceitos",
      "aceitos": ["Ensino médio", "Tecnólogo", "Bacharelado"]
    }
  }
}
```

`limitesInclusivos` não é campo persistido: a regra é sempre inclusiva (secção 1). `escolaridade.configuracao` vazia ou `aceitos: []` com `ativo: true` é configuração incompleta.

Versão: cada save gera `criteriosVersao` (ex.: `crt_det_01`). A decisão guarda essa referência e um snapshot do JSON acima, para o resultado permanecer explicável se o operador editar a tela depois.

### 10.2 `DecisaoTriagem` (exemplo inelegível por cargo e idade)

```json
{
  "candidatoId": "12:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "projetoId": "prj_01",
  "resultado": "inelegivel",
  "motivos": [
    {
      "criterio": "cargo",
      "codigo": "cargo_fora_da_lista",
      "valorLido": "Vendedor Externo",
      "valorComparado": "vendedor externo",
      "esperado": ["Analista de dados"],
      "mensagem": "Último cargo \"Vendedor Externo\" (comparado como \"vendedor externo\") não está na lista de cargos aceitos: Analista de dados."
    },
    {
      "criterio": "idade",
      "codigo": "idade_fora_da_faixa",
      "valorLido": "51",
      "valorComparado": "51",
      "esperado": { "minima": 18, "maxima": 45 },
      "mensagem": "Idade 51 está fora da faixa 18 a 45 (limites inclusivos)."
    }
  ],
  "criteriosInativos": ["escolaridade"],
  "criteriosVersao": "crt_det_04"
}
```

O hash do exemplo é ilustrativo.

### 10.3 O que esta etapa não preenche

`CriteriosQualitativos`, `PromptDoProjeto`, `AvaliacaoIa`, execução de `PedidoTrajetoria`. Não lê resposta de chatbot para decidir elegibilidade.

---

## 11. Critérios de aceite (Given / When / Then)

Não são testes automatizados. O implementador pode traduzi-los depois.

### CA-01 — Cargo fora da lista ativa

Given um projeto com critério de cargo **ativo** e lista aceita `["Analista de dados"]`, demais critérios inativos  
And um candidato cujo último cargo lido é `"Vendedor"`  
When a triagem é executada  
Then o resultado é `inelegivel`  
And há um motivo `cargo_fora_da_lista` que cita o cargo lido `"Vendedor"` e a lista não atendida `Analista de dados`

### CA-02 — Cargo na lista e demais ativos satisfeitos

Given cargo ativo com lista `["Analista de dados"]`, idade ativa 18–45, escolaridade ativa com `["Bacharelado"]`  
And candidato com último cargo `"Analista de dados"`, idade `34`, escolaridade `"Bacharelado"`  
When a triagem é executada  
Then o resultado é `elegivel`  
And `motivos` está vazia

### CA-03 — Idade abaixo do mínimo

Given idade ativa com mínima `18` e máxima `45`  
And candidato com idade `17` e demais critérios ativos satisfeitos  
When a triagem é executada  
Then o resultado é `inelegivel`  
And há motivo `idade_fora_da_faixa`

### CA-04 — Idade acima do máximo

Given idade ativa com mínima `18` e máxima `45`  
And candidato com idade `46` e demais critérios ativos satisfeitos  
When a triagem é executada  
Then o resultado é `inelegivel`  
And há motivo `idade_fora_da_faixa`

### CA-05 — Limites inclusivos não eliminam por idade

Given idade ativa com mínima `18` e máxima `45`  
And um candidato com idade `18` e outro com idade `45`, demais critérios ativos satisfeitos  
When a triagem é executada  
Then nenhum dos dois é `inelegivel` **por idade**  
And não há motivo `idade_fora_da_faixa` nesses dois

### CA-06 — Escolaridade fora da lista

Given escolaridade ativa com aceitos `["Bacharelado"]`, demais critérios inativos  
And candidato com escolaridade lida `"Ensino médio"`  
When a triagem é executada  
Then o resultado é `inelegivel`  
And há motivo `escolaridade_fora_da_lista`

### CA-07 — Cargo inativo não elimina

Given critério de cargo **inativo**, lista preenchida ou não com `["Analista de dados"]`  
And candidato com último cargo `"Vendedor"`  
And demais critérios inativos  
When a triagem é executada  
Then o resultado é `elegivel`  
And `criteriosInativos` contém `cargo`  
And a tela mostra cargo como **não aplicado**

### CA-08 — Ativo sem configuração não executa

Given critério de cargo **ativo** e `aceitos` vazio  
When o operador dispara a triagem  
Then a execução do lote é bloqueada  
And a mensagem cita o critério de cargos aceitos  
And nenhum candidato é marcado elegível  
And nenhuma `DecisaoTriagem` nova é gravada

### CA-08b — Escolaridade ativa vazia

Given escolaridade **ativa** e lista aceita vazia  
When o operador dispara a triagem  
Then a execução é bloqueada e a mensagem cita escolaridade

### CA-08c — Idade ativa sem faixa

Given idade **ativa** sem mínima ou sem máxima  
When o operador dispara a triagem  
Then a execução é bloqueada e a mensagem cita idade

### CA-09 — Inelegível não entra na avaliação por IA

Given um candidato com `DecisaoTriagem.resultado = inelegivel`  
When a tela de resultado desta etapa é exibida  
Then essa linha não é descrita como entrada da avaliação por IA  
And não há ação habilitada de avaliar por modelo nessa pessoa  
And o envelope de leitura é `inelegivel` com motivos

### CA-10 — Maiúsculas e acento não eliminam sozinhos

Given cargo ativo com lista `["Análise de Dados"]`  
And candidato com último cargo lido `"analise de dados"`  
When a triagem é executada  
Then esse critério de cargo **passa**  
And o resultado mostra valor original `"analise de dados"` e valor comparado (sem acento, minúsculo) ao lado do item da lista também na forma comparada

### CA-11 — Primeira palavra não substitui o cargo completo

Given cargo ativo com lista `["Vendedor"]`  
And candidato com último cargo `"Vendedor Externo"`  
When a triagem é executada  
Then o resultado é `inelegivel` por `cargo_fora_da_lista`  
And a comparação usou o texto completo, não `"Vendedor"` extraído como primeira palavra

### CA-11b — Lista com cargo completo aceita o texto completo

Given cargo ativo com lista `["Vendedor Externo"]`, demais inativos  
And candidato `"Vendedor Externo"`  
When a triagem é executada  
Then o resultado é `elegivel`

### CA-12 — Dado obrigatório ausente

Given cargo ativo  
And linha com último cargo em branco  
When a triagem é executada  
Then o candidato é `inelegivel`  
And o motivo tem código `dado_obrigatorio_ausente_ou_invalido` no critério cargo  
And a mensagem deixa claro que é dado obrigatório ausente ou inválido  
And o candidato **não** é `elegivel`

### CA-13 — Idade ilegível

Given idade ativa 18–45  
And célula de idade `"vinte"`  
When a triagem é executada  
Then `inelegivel` com `dado_obrigatorio_ausente_ou_invalido` no critério idade

### CA-14 — Todos os motivos, não só o primeiro

Given os três critérios ativos e configurados  
And candidato com cargo fora da lista, idade abaixo do mínimo e escolaridade fora da lista  
When a triagem é executada  
Then `motivos` contém três itens (cargo, idade, escolaridade)

### CA-15 — Sem projeto

Given nenhuma sessão com projeto aberto  
When o operador tenta importar ou executar triagem  
Then a ação é recusada com “Abra ou crie um projeto para continuar.”

### CA-16 — Sem arquivo

Given projeto aberto  
When o operador confirma importação sem arquivo  
Then recusa com “Selecione um arquivo CSV ou XLSX para importar.”

### CA-17 — UTF-8 válido

Given um CSV UTF-8 com acentos corretos no cabeçalho ou nas células  
When o operador escolhe encoding `utf-8` e importa  
Then as colunas e a pré-visualização mostram os acentos corretos  
And a importação não converte o arquivo para latin-1

### CA-18 — Mínima maior que máxima

Given idade ativa com mínima `40` e máxima `30`  
When o operador tenta salvar ou executar  
Then a faixa inválida não é persistida no save  
And a execução, se tentada, é bloqueada com a mensagem da secção 9

### CA-19 — Lista com vazio e duplicata

Given o operador inclui `""`, depois `"Analista"`, depois `"analista"` no bloco de cargos  
When a lista é atualizada  
Then o vazio é ignorado com aviso  
And o duplicado (após normalização) não entra, com aviso  
And resta um item `"Analista"`

### CA-20 — Planilha sem candidatos

Given arquivo só com cabeçalho, ou só com linhas vazias  
When o operador confirma a importação  
Then recusa com “O arquivo não contém linhas de candidato.”

### CA-21 — Reutilizar projeto

Given um projeto com critérios duros já configurados  
When o operador reutiliza/duplica  
Then existe um novo projeto com os mesmos critérios duros  
And o lote de candidatos não é copiado

---

## 12. Pendência e conflito

O contrato compartilhado e a ADR 003 definem `candidatoId` como UUID gerado na importação; `linhaOrigem` é só metadado.

O prompt desta etapa, na ausência de CSV de amostra, define o identificador como número da linha + hash do conteúdo da linha, e o nome como opcional.

**Nesta spec, na parte em conflito, vale o prompt da etapa 1** (`candidatoId` composto). Marcado como pendência: o orquestrador ainda não alterou o contrato.

Impacto e mudança proposta: `specs/history.md`.

Nenhum outro conflito com ADR/contrato impede as regras deste prompt. Faixa inclusiva já estava no contrato. Funil Excel permanece fora (ADR 005). Nome continua fora do identificador e fora de qualquer payload de LLM (ADR 007) — esta etapa sequer chama LLM.

---

## 13. Rastreabilidade

Requisito → regra → campo de tela → dado persistido → critério de aceite.

Um requisito desta etapa só está especificado com esta linha, validação/erro e Given/When/Then.

| ID | Requisito | Regra | Campo de tela | Dado persistido | Aceite |
|---|---|---|---|---|---|
| R1 | Recusar último cargo fora da lista ativa | Secção 5.2 `cargo_fora_da_lista` | Bloco cargos, lista `aceitos`, interruptor ativo | `CriteriosDeterministicos.cargos`; `DecisaoTriagem.motivos` | CA-01, CA-11 |
| R2 | Aceitar último cargo presente na lista se o resto ativo passou | Secção 5.1 `elegivel` | Idem + blocos idade e escolaridade | `DecisaoTriagem.resultado` | CA-02, CA-11b |
| R3 | Recusar idade fora da faixa | Secção 5.3; limites inclusivos | Mínima, máxima, texto “limites inclusivos” | `idade.minima` / `idade.maxima`; motivos | CA-03, CA-04, CA-05 |
| R4 | Escolaridade por lista de valores aceitos | Secção 1.1 e 5.4 | Bloco escolaridade, lista, interruptor | `escolaridade.configuracao.aceitos` | CA-06 |
| R5 | Critério inativo não elimina | Secção 5.1 `criteriosInativos` | Interruptor inativo | `criteriosInativos`; tela “não aplicado” | CA-07 |
| R6 | Ativo vazio bloqueia execução | Secção 7 | Aviso no bloco; erro na execução | Nenhum lote de decisão novo | CA-08, CA-08b, CA-08c |
| R7 | Inelegível não alimenta IA | Secção 5.5 e 8 | Resultado sem ação de modelo | `resultado: inelegivel` | CA-09 |
| R8 | Normalização visível de maiúsculas/acento/espaço | Secção 4 | Texto da regra; original + comparado | originais nas células; comparado só na decisão/exibição | CA-10 |
| R9 | Não reduzir cargo à primeira palavra | Secção 4 e 5.2 | Lista e valor mapeado completos | `ultimoCargo` texto completo | CA-11, CA-11b |
| R10 | Operador mapeia colunas; `Cargo` só sugerido | Secção 3.2; ADR 006 | Tela de mapeamento + confirmar | `mapeamentoColunas` | (mapeamento: CA-15/16 no fluxo; R10 amarra ADR 006) |
| R11 | Encoding latin-1 e UTF-8 | Secção 3.1 | Seletor de encoding, pré-visualização | lote já decodificado | CA-17 |
| R12 | Dado ausente/inválido não é elegível | Secção 5.2–5.4 | Motivo na lista de resultado | motivo `dado_obrigatorio_ausente_ou_invalido` | CA-12, CA-13 |
| R13 | Avaliar todos os ativos | Secção 5 | Lista de motivos | `motivos[]` completo | CA-14 |
| R14 | Projeto corrente obrigatório | Secção 2.1 e 9 | Lista criar/abrir | `Projeto` | CA-15 |
| R15 | Arquivo obrigatório para importar | Secção 9 | Seletor de arquivo | — | CA-16 |
| R16 | Faixa inválida min > max | Secção 9 | Mínima, máxima | não persiste faixa invertida | CA-18 |
| R17 | Lista ignora vazio e não duplica | Secção 9 | Editor da lista + avisos | `aceitos` sem vazio/duplicata | CA-19 |
| R18 | Planilha sem candidatos | Secção 3.4 e 9 | Confirmar importação | não persiste lote vazio | CA-20 |
| R19 | Identificador estável para etapa 2 | Secção 3.3 (**pendência** UUID) | `candidatoId` / linha no resultado | `candidatoId`, `linhaOrigem`, `nomeExibicao` opcional | (contrato etapa 2; conflito no history) |
| R20 | Criar/abrir/editar/reutilizar projeto | Secção 2.1 | Telas de projeto | `Projeto` + cópia de critérios na reutilização | CA-21 |
| R21 | Guardar texto de chatbot sem julgar | Secção 3.2 | Mapeamento opcional de respostas | `respostasChatbot[]` | (sem GWT de julgamento: ausência de uso na decisão) |
| R22 | Sem token / sem LLM nesta etapa | Cabeçalho; módulo `triagem` | Sem editor de prompt; sem disparo | `DecisaoTriagem` sem score | CA-09 (fronteira) |

Validação e erro de cada linha: secção 7 e 9. Given/When/Then: secção 11.

---

## 14. Fora desta spec

- Implementar código, migração, `.env`
- Template de prompt, estimativa de token, cliente LLM
- Redesenhar funil de chatbot / `Analise [RENOMEAR].xlsx`
- Reintroduzir `LogisticRegression`, limiar 0,4, rótulo `contratado` como elegível
- Copiar `status_dentro` / `status_fora` para a tela
- Critério duro de cidade
- Autenticação

## 15. Definition of done da spec

- [x] Tela de projeto e dos três blocos, com ativo/inativo
- [x] Importação latin-1 e UTF-8, mapeamento, identificador
- [x] Comparação de cargo, idade inclusiva, escolaridade por lista
- [x] `DecisaoTriagem` com todos os motivos, inativos como não aplicado
- [x] Erros da secção 9
- [x] Given/When/Then mínimos do prompt e rastreabilidade
- [x] Conflito de `candidatoId` em `specs/history.md`, sem editar contrato do orquestrador
- [x] Sem implementação de produto
