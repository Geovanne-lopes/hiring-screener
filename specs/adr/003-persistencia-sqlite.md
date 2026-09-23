# ADR 003 — Persistência: SQLite local

## Status

Aceita.

## Problema

Projetos, critérios, prompts versionados e resultados por candidato precisam sobreviver ao fechamento do programa. O legado grava Excel solto (`Analise [RENOMEAR].xlsx`, `Resultado_modelo_ML.xlsx`) e não persiste configuração.

## Impacto

Se o único banco for a planilha importada ou o Excel de saída, a operação perde critérios, versões de prompt e o vínculo entre resultado e regra usada. Sem persistência, a avaliação deixa de ser explicável.

## Alternativas

1. Excel como único banco. Familiar à operação, frágil para versões de prompt, concorrência de escrita e consultas por candidato. Rejeitada como sistema de registro.
2. JSON/YAML em pasta. Simples, ruim para relacionar candidato, decisão, versão de prompt e uso de token.
3. PostgreSQL ou outro servidor. Desproporcional para um operador local sem autenticação.
4. SQLite em arquivo local. Sobrevive ao fechamento, não exige serviço extra, cabe no modelo de aplicação web local.

## Decisão

O sistema de registro é um arquivo SQLite no disco da máquina do operador, fora do Git.

- Caminho padrão: `./data/screener.sqlite`, sobrescrevível por variável de ambiente `SCREENER_DB_PATH`.
- A planilha de mapeamento é **fonte de importação**, não banco.
- Excel de funil do legado não é persistência (ADR 005).
- Cada avaliação por LLM guarda a versão do prompt e dos critérios qualitativos usados.
- Cada decisão de triagem guarda os critérios determinísticos usados e os motivos.

## Justificativa

O requisito é sobreviver ao fechamento e manter o resultado explicável. SQLite atende os dois sem inventar servidor, usuário de banco ou Excel como schema.

## Consequência

- O implementador cria o diretório `data/` se não existir e não versiona o `.sqlite`.
- Reimportar uma planilha no mesmo projeto substitui o lote de candidatos daquele projeto ou cria um novo lote; o detalhe do recálculo fica com o agente da etapa 1, mas o contrato já exige identificador estável por candidato **depois** da importação.
- Backup operacional = copiar o arquivo SQLite e, se desejado, a planilha original. Não há sync em nuvem nesta entrega.
