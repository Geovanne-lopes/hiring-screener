# PROMPT — AGENTE IMPLEMENTADOR DA SPRINT 1

Você implementa a primeira entrega do screener. Os agentes anteriores só escreveram especificação. Este agente escreve código.

## 1. Missão

Construir a aplicação web local descrita nas specs, com as duas etapas da sprint 1 funcionando de ponta a ponta:

1. Triagem determinística (cargos, idade, escolaridade), sem LLM.
2. Avaliação por IA das respostas do chatbot, só para quem passou na triagem e tem resposta utilizável.

A trajetória profissional não entra. O botão **Avaliar trajetória** fica visível, desabilitado, com texto de que a função vem em sprint posterior, e não dispara request.

## 2. Fontes, nesta ordem

Leia antes de criar arquivo de produto:

1. `specs/02-arquitetura.md`
2. `specs/03-contratos-compartilhados.md`
3. `specs/adr/` (001 a 007)
4. `specs/glossario.md`
5. `specs/sprint-1/triagem-deterministica.md`
6. `specs/sprint-1/avaliacao-ia-chatbot.md`
7. `specs/history.md` (pendências)
8. `specs/sprint-2/trajetoria-profissional.md` só para respeitar o que a sprint 1 não faz

Se a spec de sprint 1 e uma ADR divergirem, vale a spec da sprint 1 naquele ponto e você registra a escolha num comentário curto em `specs/history.md`. Não reabra a arquitetura.

## 3. Decisões já fechadas

Não escolha de novo.

- Aplicação web local, sem login (ADR 001).
- Interface: React 18, TypeScript, Vite, React Router, em `apps/web`. O navegador não chama o provedor de LLM.
- API: FastAPI, Uvicorn, Pydantic, Python 3.11+, em `apps/api`.
- Planilha: pandas + openpyxl. CSV com encoding escolhido pelo operador, no mínimo `latin-1` (padrão) e `utf-8`. Também XLSX.
- Regra dura: módulo `triagem`, função pura, zero HTTP. Esse módulo não importa `avaliacao_ia`.
- LLM: módulo `avaliacao_ia`, único ponto de chamada externa. Adaptador no estilo OpenAI (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES`). Sem fornecedor fixo no código. Sem scikit-learn, sem regressão logística, sem limiar 0,4.
- Persistência: SQLAlchemy 2 + SQLite em `SCREENER_DB_PATH` (padrão `./data/screener.sqlite`).
- Funil Excel do legado fica de fora (ADR 005).
- Último cargo é a coluna que o operador mapear. Se existir coluna `Cargo`, sugerir, e só seguir depois da confirmação. Não usar `Cargo Anterior` como sugestão (ADR 006).
- Nome não entra no prompt nem no log de token (ADR 007).

### Identificador do candidato

O contrato pede UUID. A spec da triagem, e o `specs/history.md`, mandam prevalecer nesta entrega o id composto: `{linhaOrigem}:{sha256hex}` do conteúdo da linha, como em `specs/sprint-1/triagem-deterministica.md` secção 3.3. Use esse formato. Não gere UUID.

## 4. O que construir

Fluxo do operador:

1. Criar, abrir, editar nome e duplicar projeto. Duplicar copia só os critérios duros, não o lote.
2. Configurar os três blocos (cargos aceitos, faixa de idade inclusiva, escolaridade por lista de valores). Cada um ativo ou inativo. Lista vazia ativa bloqueia a execução do lote inteiro. Critério inativo não elimina.
3. Importar CSV/XLSX, pré-visualizar, mapear colunas, confirmar. Reimportar substitui o lote e apaga as decisões daquele projeto.
4. Executar a triagem e ver elegível ou inelegível, com todos os motivos, valor lido e valor comparado.
5. Configurar critérios qualitativos da vaga e editar o prompt do projeto, com pré-visualização antes de gastar token.
6. Disparar a avaliação só para elegíveis com resposta. Inelegível não gera chamada. Elegível sem resposta fica aguardando, sem chamada. Falha de JSON ou de provedor não marca compatível e não apaga a triagem.
7. Ver perfil, compatibilidade, julgamento por critério, trechos, versão do prompt e tokens.

Regras de comparação, erros, estados e JSON de saída estão nas duas specs de `specs/sprint-1/`. Implemente o que elas dizem, inclusive normalização visível (trim, espaço, sem acento, minúsculas) e a proibição de reduzir o cargo à primeira palavra ou de rebaixar escolaridade a `bacharelado`.

Crie `.env.example` com as variáveis da ADR 004, valores vazios na chave. Coloque `.env` no `.gitignore`. Sem chave, a etapa 2 não dispara e a tela explica a falta de configuração.

## 5. Fora desta implementação

- Módulo `trajetoria`, endpoint `avaliar_trajetoria`, leitura obrigatória de resumo ou headline.
- Autenticação, papéis, deploy em nuvem.
- Relatório de funil do script antigo.
- Treino de modelo.
- Alterar as specs para caber num atalho. Se um detalhe da spec estiver impossível, pare nesse ponto, descreva o bloqueio e não invente outra regra.

## 6. Pronto quando

- `triagem` tem testes automatizados dos critérios de aceite CA-01 a CA-14 de `triagem-deterministica.md` (cargo fora da lista, faixa inclusiva, escolaridade, critério inativo, lista vazia bloqueia, primeira palavra não substitui o cargo, dado ausente).
- A API sobe em localhost e o frontend abre no navegador.
- Dá para criar um projeto, importar uma planilha pequena, triar e ver o motivo, sem nenhuma chamada de LLM.
- A avaliação por IA recusa o lote quando a chave está vazia, e o código do cliente só é alcançado para elegível com resposta.
- O botão Avaliar trajetória não chama a API.

Não declare a entrega pronta só com a tela estática. Rode o fluxo de triagem de verdade.
