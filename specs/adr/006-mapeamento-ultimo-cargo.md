# ADR 006 — Qual campo da planilha é o último cargo

## Status

Aceita.

## Problema

O código vigente lê a coluna `Cargo`. `Cargo Anterior` aparece só como parâmetro morto em `cargo_preprocessing(..., cargo_anterior=False)` e não é usado pelos callers. Não há CSV local no Git nem no disco analisado para listar colunas reais de resposta ou de histórico. Reduzir o cargo à primeira palavra é a regra vigente do legado e não pode ser a regra padrão do sistema novo.

## Impacto

Se o contrato assumir `Cargo Anterior` como coluna existente, a importação quebra em planilhas reais. Se assumir “primeira palavra de `Cargo`”, a vaga muda de significado. Se o sistema escolher a coluna sozinho, a operação perde o controle que o produto novo existe para devolver.

## Alternativas

1. Tratar `Cargo Anterior` como coluna obrigatória. Rejeitada: só existe em comentário/parâmetro não usado.
2. Sempre usar `Cargo` e fatiar a primeira palavra. Rejeitada como regra de elegibilidade.
3. O operador mapeia, na importação, qual coluna do arquivo é o último cargo. Se o arquivo só tiver `Cargo`, essa coluna é o último cargo.

## Decisão

O último cargo é **o valor da coluna mapeada pelo operador** na importação, sem redução à primeira palavra e sem taxonomia embutida no código.

- Se a planilha tiver uma coluna chamada `Cargo` e o operador não escolher outra, `Cargo` é o último cargo.
- `Cargo Anterior` só entra se existir no arquivo **e** for mapeada explicitamente. Comentário no legado não cria coluna.
- O texto completo mapeado é o que a etapa 1 compara com a lista de cargos aceitos. Sinônimos, gênero e tradução solta do legado não são regra padrão.
- Não há CSV versionado neste repositório. Busca local por `*.csv`/`*.xlsx` em `data-visualization-carrefour` não retornou arquivo. Nomes de coluna de **respostas de chatbot** não são inventados: o operador mapeia uma ou mais colunas de texto como respostas, quando existirem no arquivo.

## Justificativa

O código mostra `Cargo` em uso e `Cargo Anterior` só em ramo morto. O prompt do orquestrador já fechou o contrato de importação: o operador mapeia a coluna; ausência de CSV local impede inventar schema de respostas.

## Consequência

- `CandidatoImportado.ultimoCargo` é string (texto mapeado), obrigatória para executar a triagem se o critério de cargo estiver ativo.
- Agente 1 detalha comparação (igualdade, lista, normalização mínima de maiúsculas/acento). Não reintroduz `just_first_split=True` como padrão.
- Agente 2 não usa cargo como substituto das respostas do chatbot.
- Agente 3 poderá pedir outros campos de trajetória depois; isso não altera o mapeamento de último cargo da primeira entrega.
