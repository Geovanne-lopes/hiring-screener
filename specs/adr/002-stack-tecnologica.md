# ADR 002 — Stack tecnológica

## Status

Aceita.

## Problema

O legado é Python, mas isso não obriga a stack nova. Os agentes implementadores não podem escolher framework de novo. Interface, regra determinística, cliente de LLM e persistência precisam ficar separados. A chamada ao LLM não pode misturar-se com idade, cargo ou escolaridade.

## Impacto

Uma stack ambígua gera retrabalho e mistura etapa 1 com etapa 2. Uma stack rígida demais (um único arquivo Streamlit, por exemplo) impede o contrato entre etapas.

## Alternativas

1. Streamlit ou Gradio. Tela rápida, mas o editor de prompt, o encadeamento de duas etapas e a persistência versionada ficam forçados. Rejeitada.
2. Desktop Python (PySide). Tela nativa, pior para editor de texto longo e para navegação entre etapas.
3. Monólito TypeScript (Next.js full-stack). Um só idioma, mas o import de CSV `latin-1` e Excel é mais trabalhoso do que no ecossistema pandas, que o legado já usa para ler o mapeamento.
4. Frontend React/TypeScript + backend FastAPI, com módulos internos isolados. Um idioma na tela, Python só no servidor, fronteiras explícitas.

## Decisão

Stack obrigatória da primeira entrega:

| Camada | Tecnologia | Pode chamar LLM? |
|---|---|---|
| Interface | React 18, TypeScript, Vite, React Router | Não |
| API HTTP | FastAPI, Uvicorn, Pydantic, Python 3.11+ | Não diretamente |
| Importação de planilha | pandas + openpyxl | Não |
| Regra determinística | Módulo `triagem` no backend, sem cliente HTTP | Não |
| Cliente de LLM | Módulo `avaliacao_ia`, único ponto de chamada externa | Sim, só depois de `elegivel` com resposta utilizável |
| Persistência | SQLAlchemy 2 + SQLite (ADR 003) | Não |

O frontend não chama o provedor de LLM. A API orquestra. `triagem` não importa `avaliacao_ia`.

## Justificativa

A tela precisa de um editor de prompt e de formulários por projeto. React+Vite cobre isso sem o implementador escolher UI kit de novo. O backend em FastAPI isola a regra dura da chamada paga. pandas continua sendo o leitor de CSV `latin-1` e XLSX, que é o formato real do mapeamento.

Não se usa regressão logística, limiar 0,4, one-hot nem scikit-learn no sistema novo.

## Consequência

- Agentes de etapa não escolhem outro framework de UI, API, ORM ou cliente HTTP.
- Implementar a etapa 1 significa regras em `triagem` + telas de critérios/importação/execução.
- Implementar a etapa 2 significa `avaliacao_ia` + telas de critérios qualitativos, editor de prompt e disparo.
- A etapa 3 não ganha módulo executável na primeira entrega; só o ponto de navegação desabilitado.
