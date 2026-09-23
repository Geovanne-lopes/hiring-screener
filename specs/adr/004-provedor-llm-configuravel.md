# ADR 004 — Provedor de LLM configurável

## Status

Aceita.

## Problema

A etapa 2 envia respostas de chatbot a um LLM. O legado não tem LLM. Fixar um fornecedor porque outro desafio usou um modelo específico acopla o produto a uma conta e a uma API. A chave não pode entrar no Git.

## Impacto

Provedor hardcoded impede troca de conta, modelo e endpoint. Sem timeout, retry limitado e tratamento de resposta inválida, a operação fica presa a chamada travada ou a JSON quebrado. Sem registro de token, o custo some.

## Alternativas

1. Fixar um fornecedor (Gemini, OpenAI, Anthropic, etc.) no código. Rejeitada.
2. Fine-tuning ou treino próprio com a coluna `Status`. Fora de escopo; o legado de regressão logística não evolui.
3. Cliente HTTP compatível com API estilo OpenAI (`base_url` + `api_key` + `model`), configurado por ambiente.

## Decisão

O cliente de LLM é um adaptador único, configurável por variável de ambiente, com saída estruturada (JSON com schema). Não há fornecedor obrigatório.

Comportamento exigido do cliente:

- timeout configurável
- retry limitado (não infinito)
- recusa de resposta que não valide o schema; o candidato fica com estado de falha explicável, sem inventar perfil
- registro de uso de token (entrada, saída, total) por avaliação, persistido com a versão do prompt
- nenhuma chamada se a triagem for `inelegivel`
- nenhuma chamada se o candidato for `elegivel` e não tiver resposta de chatbot utilizável

Desenho do `.env.example` (não criar o arquivo de ambiente real; chave vazia):

```
# Persistência local
SCREENER_DB_PATH=./data/screener.sqlite

# LLM — preencher localmente; nunca versionar valor real de LLM_API_KEY
LLM_BASE_URL=https://api.example.com/v1
LLM_API_KEY=
LLM_MODEL=
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
```

A chave não entra no Git. `.env` fica no ignore. Sem esses valores, a etapa 2 não dispara e explica o erro na tela.

## Justificativa

A spec precisa de um LLM de verdade na etapa 2, não de um fornecedor de outro projeto. Endpoint + modelo + chave por ambiente deixa a operação escolher a conta. Timeout, retry, schema e token tornam a chamada operacional, não um experimento.

## Consequência

- Agente 2 detalha o schema da saída (`AvaliacaoIa`) e o editor de prompt; não escolhe SDK de um cloud específico como obrigatório.
- Implementador usa um cliente HTTP genérico (por exemplo `httpx`) contra `LLM_BASE_URL`. Biblioteca oficial de um fornecedor só é aceitável se permanecer atrás desse adaptador e não vazar nomes de produto para a tela.
- Não há fallback silencioso para a regressão logística.
