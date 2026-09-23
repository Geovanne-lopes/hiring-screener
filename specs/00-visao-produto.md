# Visão do produto — triagem de candidatos

## Por que o sistema existe

A pessoa que mantinha o repositório legado saiu. A operação precisa recuperar o controle da regra de triagem e da evolução do produto. O legado é fonte de comportamento e de lacunas. Não é a base de código a estender.

O produto continua a operação de **triar um mapeamento de candidatos (planilha de recrutamento) contra uma vaga/projeto, com resultado por pessoa**. O método muda.

## O que muda em relação ao legado

| Legado | Sistema novo |
|---|---|
| Script de terminal | Aplicação web local com tela (ADR 001) |
| Listas de status e sinônimos no código | Critérios duros editáveis por projeto, na tela |
| Funil Excel e/ou regressão logística | Resultado por candidato: inelegibilidade ou perfil + compatibilidade |
| Não lê texto das respostas do chatbot | Etapa 2 envia respostas utilizáveis a um LLM |
| `--dev_mode`, colunas e arquivos fixos | Operador mapeia colunas na importação |
| Rótulo interno `contratado` | Vocabulário do glossário: inelegível, elegível na triagem, compatível/parcial/incompatível |

## Recorte da primeira entrega

Duas etapas encadeadas. A terceira existe no mapa e não roda.

### Etapa 1 — Triagem determinística (implementar)

Tela para cadastrar, por projeto/vaga, critérios básicos de aceite ou recusa. Exemplo obrigatório:

- cargos aceitos
- faixa de idade
- escolaridade

Regras congeladas neste recorte (detalhe da comparação de escolaridade: agente 1):

- último cargo fora da lista de cargos aceitos → inelegível
- idade fora da faixa → inelegível
- escolaridade entra na mesma tela; a comparação (lista permitida, nível mínimo, ou os dois) não passa para o LLM
- critério **ativo** com configuração vazia **impede a execução** e explica o erro
- critério **inativo** não elimina ninguém
- lista vazia **não** significa “aceitar todos” em silêncio
- esta etapa não chama LLM e não consome token

### Etapa 2 — Avaliação das respostas do chatbot por LLM (implementar)

Roda depois da etapa 1, somente para quem a triagem marcou `elegivel` **e** quem tem resposta de chatbot utilizável.

- inelegível → não vai para o modelo
- elegível sem resposta → fica **aguardando**, sem chamada de API

A tela desta etapa precisa dos dois mecanismos:

1. campos para inserir e atualizar os critérios qualitativos daquela vaga
2. editor do prompt enviado ao LLM (é o que consome token)

Critérios estruturados e texto do prompt são salvos por projeto. A avaliação guarda a versão usada, para o resultado ser explicável.

O legado não tem LLM. Não evoluir a regressão logística. Sem fine-tuning e sem treino de modelo na primeira entrega.

### Etapa 3 — Trajetória profissional (fora da implementação inicial)

Outro botão, outra função. A partir de cargos, resumos e headlines, traçar perfil da trajetória e comparar com a vaga. O agente 3 especifica. As etapas 1 e 2 não dependem dela. Na primeira entrega o botão aparece desabilitado, com o texto de que a função vem em sprint posterior, e **não dispara modelo**.

## Fluxo operacional congelado

1. Criar ou abrir um projeto.
2. Configurar critérios duros.
3. Importar a planilha e mapear colunas.
4. Executar a triagem determinística.
5. Para elegíveis com resposta, configurar critérios qualitativos e revisar o prompt.
6. Executar a avaliação por LLM.
7. Ver o resultado por candidato.

## O que “fazer a mesma coisa” significa

Continuar a triar mapeamento contra vaga, com resultado por pessoa.

Não significa reproduzir o Excel de funil, o `--dev_mode`, nem o rótulo `contratado`. O funil legado fica fora da primeira entrega (ADR 005).

## Fora de escopo (todos os agentes)

- Implementar tela, API, script, modelo ou importador neste chat de spec
- Copiar listas de status do legado para dentro do LLM e chamar isso de critério
- Autenticação multi-usuário, papéis, JWT, trilha de auditoria corporativa
- Treinar modelo próprio com a coluna histórica `Status`
- Implementar avaliação por trajetória na primeira entrega
- Aplicativo Android, gestão de inovação, papéis OPERATOR/MANAGER/LEADER, Room, Retrofit, MongoDB ou Gemini obrigatório — domínio de outro desafio, proibido aqui

## Critérios de aceite deste recorte (arquitetura, não da regra de tela)

Estes critérios amarram o produto. Given/When/Then de widget, de comparação de escolaridade e de texto de prompt pertencem aos agentes 1 e 2.

1. Dado um candidato `inelegivel`, quando a avaliação por IA é disparada, então nenhuma chamada externa é permitida.
2. Dado um candidato `elegivel` sem resposta de chatbot utilizável, quando a avaliação por IA é disparada, então o candidato permanece aguardando e nenhuma chamada externa é permitida.
3. Dado um critério duro ativo com configuração vazia, quando a triagem é executada, então a execução é bloqueada e o erro é explicado; ninguém é aceito em silêncio.
4. Dado um critério duro inativo, quando a triagem é executada, então esse critério não elimina ninguém.
5. Dado o botão de trajetória na primeira entrega, quando o operador o vê, então ele está desabilitado, informa sprint posterior e não dispara modelo.
6. Dado o fechamento e a reabertura do programa, quando o operador abre o mesmo projeto, então critérios, prompts versionados e resultados persistidos ainda estão lá (ADR 003).

## Fontes

- Código legado listado em `specs/01-legado-e-gaps.md`
- ADRs em `specs/adr/`
- Contratos em `specs/03-contratos-compartilhados.md`
- Glossário em `specs/glossario.md`
