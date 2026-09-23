# Legado e lacunas

Fonte analisada: `D:\Backup\Pasta-Documentos\2-Estudos\Projetos Hiring\data-visualization-carrefour\data-visualisation-carrefour`.

O retrato abaixo foi confirmado no código. Onde o prompt do orquestrador resumia o legado, o código prevalece; as correções pontuais estão marcadas.

## O que existe neste repositório legado

| Item | Situação |
|---|---|
| `README.md` | Só o título `# data-visualisation-carrefour`. Não há documentação de uso. |
| `data_vis_carrefour.py` | Pipeline de terminal: funil por coluna → Excel |
| `packages/data_preprocessing.py` | Normalização, faixas, taxonomias, Excel writer |
| `model_ml.py` | Treino e predição de regressão logística |
| `.gitignore` | Ignora `*.csv`, `*.xlsx`, `__pycache__/`, `build/`, `dist/`, `*.spec`, `Performance_Analysis_Apresentacao/`, `merge-spreadsheets/` |
| Teste automatizado | Não existe |
| Tela, autenticação, banco, API | Não existem |
| Pasta `specs/` no legado | Não existe |
| CSV/XLSX versionado | Não existe |

Busca local por `*.csv` e `*.xlsx` nesse diretório e no pai `data-visualization-carrefour` **não encontrou arquivo**. Não há colunas reais de respostas de chatbot para registrar. Nomes de coluna de resposta **não foram inventados**.

Caminhos de CSV citados no código (não presentes no disco analisado):

- `Database\\final_ddn_dataset.csv` (`--dev_mode` e treino do modelo)
- `Database\\27-01-2025 - Projeto DDN 39 Vagas - Cielo - Fagner(Mapeamento).csv` (base nova da predição)
- `Database\\Mapeamentos Pilotos - Carrefour - BI(Mapeamento Stand).csv` (linha comentada)

## O que o legado faz de fato

É um pipeline Python de terminal, sem tela.

### `data_vis_carrefour.py`

1. Procura um CSV na **pasta pai** do script (`glob` `\\*.csv`), lê com encoding `latin-1`.
2. Pergunta quais colunas analisar (separadas por vírgula, sem espaços) e valida contra os nomes do arquivo (com strip).
3. Se existem `Status` e `Status Chatbot`, pergunta qual é o alvo. Se só uma existe, escolhe essa.
4. Se o alvo é `Status Chatbot`, extrai datas do próprio valor da coluna (`split` em `-`, segundo token, formato `%d/%m/%Y`), pergunta quais datas ou `TODOS`.
5. Sem `--dev_mode`, devolve subset, alvo, datas e dataframe.
6. Com `--dev_mode`: colunas fixas `Cargo`, `Idade`, `Cidade`, `Atualização CV`; alvo `Status`; lista de datas fixas; lê `Database\\final_ddn_dataset.csv`.
7. Chama `initial_preprocessing`, depois `idade_preprocessing`, `cidade_preprocessing`, `cargo_preprocessing(..., split=True)` e `escolaridade_preprocessing` **sempre**, independentemente das colunas escolhidas.
8. Para cada coluna do subset, monta tabela de funil; acrescenta um breakdown global; grava `Analise [RENOMEAR].xlsx`.

Funil de `Status Chatbot` (`get_working_spreadsheet`):

- `Enviado`, `Respondeu`, `Elegível`
- `Taxa de Resposta (%)` = Respondeu / Enviado
- `Taxa Elegível (%)` = Elegível / Respondeu
- ordena por taxa de resposta
- “Respondeu” = linhas com `Status Chatbot == 'Respondido'`
- “Elegível” no funil = dessas, `Elegível == 'Elegível'`

Breakdown de `Status Chatbot` (`get_cuts_breakdown`): soma `Respondido` em `Enviado` para o total enviado incluir quem já respondeu; concatena a contagem da categoria `Elegível` da coluna `Elegível`; calcula `Corte %` via `pct_change`.

Funil de `Status`:

- `Candidatos` vs `Dentro do Perfil`
- Excel nomeia a taxa `Taxa de Contratação (%)`
- “Dentro do Perfil” = linhas cujo `Status` já foi colapsado para o rótulo interno `contratado`

O rótulo interno `contratado` **não significa pessoa contratada**. Ver `initial_preprocessing` abaixo.

### `packages/data_preprocessing.py`

`initial_preprocessing`:

- remove linhas totalmente vazias; dá strip nos nomes de coluna
- normaliza texto das colunas do `working_set` (NFKD, sem acento, minúsculas)
- parâmetro `date_subset` existe e filtra `Status Chatbot` se diferente de `['TODOS']`
- `Status Chatbot`: se `inclui_sem_interesse_respondido` é falso (único valor passado pelos callers), quem tem `Elegível` contendo `Sem Interesse` é reclassificado para `Status Chatbot = Enviado`; depois qualquer valor contendo `Enviado` ou `Respondido` é colapsado nesses dois rótulos
- `Status`: lista `status_dentro` vira `contratado`; `status_fora` vira `fora do perfil`; `status_desconsidera` vira `desconsiderar model ml` e sai da análise. A classificação usa `str.contains`, não igualdade exata
- sem alvo (`has_target=False`, usado na predição em base nova): filtra `Equipe` ∈ `['Novos - 12/05', 'Novos - 14/05', 'Novos - 16/05', 'Novos  - 29/01', 'Novos  - 30/01']`
- **retorno: só o dataframe**. Não devolve índice original

`idade_preprocessing`: numérico coercível; faixas `Ate 18`, `19 a 24`, `25 a 29`, `30 a 34`, `35 a 39`, `40 a 44`, `45 a 49`, `Acima de 50` (`right=False`).

`cidade_preprocessing`: reescreve ocorrências contendo `embu`, `osanco` (sic, para `osasco`), `balneario`.

`cargo_preprocessing` (regra vigente, não o bloco comentado):

- pontuação → espaço
- stop words (`de`, `ao`, `e`, `ii`)
- unificação de gênero e algumas traduções
- `gns` → `gestor` e, na mesma lista, `gestor` → `gerente`
- por padrão `split=True` e `just_first_split=True`: **fica só a primeira palavra**
- parâmetro `cargo_anterior=False` escolheria a coluna `Cargo Anterior`; **nenhum caller passa True**

Blocos grandes comentados (“CARREFOUR STAND”, agrupamentos por área, máscara “FOR CONTACT”) são experimento abandonado, não regra vigente.

`escolaridade_preprocessing`:

- pega o trecho antes de ` · `
- agrupa por substring (`bacharelado`, `mba`/`mestrado`/`pos` → `pos-graduacao`, `tecnologo`, `ensino medio`, etc.)
- **`'graduacao'` e `'gradu'` são mapeados para `pos-graduacao`** no código vigente
- `#name?` vira NA; anos de quatro dígitos são removidos
- categorias com **5 ocorrências ou menos** viram `bacharelado` (comentário no código diz “less than 10”; o corte real é `<= 5`)

`create_excel`: uma aba `Analise`, várias tabelas empilhadas, breakdown à direita, arquivo `Analise [RENOMEAR].xlsx`.

### `model_ml.py`

Não é um LLM.

- treina `LogisticRegression(class_weight='balanced')` com one-hot (`OneHotEncoder(min_frequency=2, handle_unknown='ignore')`) de `Idade`, `Cargo` e `Escolaridade`
- alvo: coluna `Status` já colapsada
- limiar **0,4** sobre `predict_proba[:, 0]` rotulado como classe `contratado` (a ordem das colunas de probabilidade segue `clf.classes_`, tipicamente alfabética)
- grava `ANÁLISE - INDICAÇÃO PERFIL BI - AI` como `Sim` ou `Nao` em `Resultado_modelo_ML.xlsx` (só essa coluna)
- predição em base nova filtra equipes `Novos` de datas fixas (via `initial_preprocessing(..., has_target=False)`)
- validação cruzada, coeficientes e matriz de confusão estão comentados ou desligados no `main`
- `sklearn.svm`, `DecisionTreeClassifier` e vários métricos são importados e não usados no fluxo ativo

## Listas de status usadas para o rótulo `contratado`

Isso é acidente de implementação do modelo/funil. **Não é critério do sistema novo.**

Colapsam para `contratado` (entre outros): Ligar, Enviar Chatbot, Finalista em várias grafias, Aprovado DG, Sem interesse, CONTRATADO, Standby, invited, fechada, reprovado gestor, declinou, congelada, etc.

Colapsam para `fora do perfil`: DESCONSIDERAR, Reprovado Pesquisa, Fora do perfil, Reprovado DG, reprovado teste.

Saem da análise (`desconsiderar model ml`): base nova - avaliar, telefone não localizado, ex cielo, aberta.

`status_unique = df['Status'].unique().tolist()` é calculado e nunca usado.

## Colunas vistas em código vigente (não comentado)

| Coluna | Onde |
|---|---|
| `Cargo` | funil, modelo, pré-processamento |
| `Idade` | idem |
| `Cidade` | funil em `--dev_mode`, pré-processamento sempre chamado |
| `Atualização CV` | só `--dev_mode` como coluna de funil |
| `Escolaridade` | modelo e pré-processamento |
| `Status` | alvo funil/modelo |
| `Status Chatbot` | alvo funil; datas extraídas do próprio valor |
| `Elegível` | funil chatbot; contém pelo menos `Elegível` e `Sem Interesse` |
| `Equipe` | filtro de base nova no modelo |

Colunas **somente em comentário** (não tratar como existentes): `Cargo Anterior`, `Nome`, `Justificativa`.

O código **não lê texto de respostas de chatbot**. Só conta status (`Enviado` / `Respondido` / `Elegível`).

## Regras de negócio que ainda valem (intenção, não o bug)

- A operação trabalha sobre um **mapeamento** (planilha) de um processo/vaga.
- Há atributos de candidato usados na prática: cargo, idade, escolaridade (e, no funil, cidade).
- Há um ciclo de chatbot com estados de envio, resposta e uma flag de elegibilidade operacional distinta do status de processo.
- O resultado útil é **por conjunto de candidatos de um mapeamento**, não um modelo genérico de mercado.
- Encoding real de leitura no legado: `latin-1`.

## Acidente de implementação, código morto e bug (não preservar como requisito)

1. **Unpacking quebrado.** `data_vis_carrefour.py` faz `df, og_index = initial_preprocessing(...)`, mas a função retorna só o dataframe. Isso explode em runtime. Não há `og_index`.
2. **Datas do chatbot não filtram.** `DATE_SUBSET` é perguntado e guardado; `initial_preprocessing` é chamado sem `date_subset`. O default interno é `['TODOS']`. O filtro efetivo fica em todas as datas.
3. **Pré-processamento ignora a escolha de colunas.** Idade, cidade, cargo e escolaridade são processados mesmo quando a coluna não foi escolhida. Se a coluna não existir no CSV, a chamada quebra.
4. **Não lê respostas do chatbot.** Só agrega status. Lacuna de produto, não feature.
5. **Critério não é editável.** Listas de status, sinônimos de cargo, faixas de idade e agrupamento de escolaridade estão no código.
6. **Primeira palavra do cargo.** Muda o significado da vaga. Proibido como regra padrão nova (ADR 006).
7. **Escolaridade rara → `bacharelado`.** Não pode ser regra de elegibilidade.
8. **`graduacao` → `pos-graduacao`.** Defeito vigente no dicionário; não copiar.
9. **`gestor` → `gerente`** e `osanco` no lugar de um match de Osasco: taxonomia frágil.
10. **`contratado` no funil/modelo** mistura “ligar”, “standby”, “sem interesse” e “contratado” real. O Excel ainda chama isso de taxa de contratação.
11. **Filtro `Equipe` com datas literais** na predição de base nova: acoplamento a um projeto específico (Cielo/DDN), não regra geral.
12. **`inclui_sem_interesse_respondido=True` nunca é usado** pelos callers.
13. **Taxonomias comentadas de cargo:** código morto.
14. **Validação cruzada, coeficientes, matriz de confusão:** desligados.
15. **`--dev_mode`:** atalho de desenvolvedor, não produto.
16. **Predição grava só a coluna de Sim/Nao** em Excel novo, sem motivos.
17. **`predict_at_thold` usa a coluna 0 de `predict_proba`**, não um acesso explícito à classe `contratado`. Comportamento depende da ordem de `classes_`.

## O que a spec do sistema novo não deve preservar

- Funil Excel como fluxo principal (ADR 005)
- Regressão logística, limiar 0,4, one-hot, scikit-learn
- Colapsar status de processo em `contratado` / `fora do perfil`
- Reduzir cargo à primeira palavra
- Jogar escolaridade rara em `bacharelado`
- Datas pedidas e ignoradas
- Filtros de equipe com datas cravadas
- Qualquer bug acima como “regra de negócio”

## Lacunas que o sistema novo precisa cobrir (sem detalhar tela aqui)

- Tela e persistência de critérios por projeto
- Importação com mapeamento de colunas, inclusive último cargo e textos de chatbot quando existirem no arquivo
- Triagem determinística com motivos por pessoa
- Avaliação por LLM só para elegíveis com resposta utilizável
- Versionamento de prompt
- Identificador estável do candidato (o legado não tem chave única vigente; o índice do pandas é acidente)
- Coluna de nome: não confirmada no código vigente; o operador pode mapear se existir (ADR 007)
