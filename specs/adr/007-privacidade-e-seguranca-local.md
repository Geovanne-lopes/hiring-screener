# ADR 007 — Privacidade do payload LLM e segurança local

## Status

Aceita.

## Problema

A etapa 2 envia texto a um provedor externo. O mapeamento contém dados de candidatos. O legado não tem autenticação, papéis, JWT nem trilha de auditoria. É preciso dizer o que pode ir ao LLM, o que não vai, e o que a ferramenta assume como modelo de uso.

## Impacto

Mandar a planilha inteira, inclusive inelegíveis, vaza dado que não participa do julgamento e gera custo. Mandar o nome no prompt identifica a pessoa no fornecedor sem necessidade de julgamento. Inventar login agora copia outro produto e foge do legado.

## Alternativas

1. Enviar o registro completo do candidato, inclusive nome, cidade, equipe e status interno. Rejeitada: excesso e mistura com dados que não julgam a vaga.
2. Autenticação multi-usuário, papéis OPERATOR/MANAGER/LEADER, JWT. Rejeitada: não existe no legado; a ferramenta é de quem opera a triagem.
3. Mínimo necessário no prompt: respostas de chatbot utilizáveis + critérios qualitativos da vaga + template. Identificador estável no lugar do nome. Resultado nominado só na persistência local, se o operador mapeou uma coluna de nome.

## Decisão

### Uso

A ferramenta é **monoposto local**. Quem sobe o processo na máquina opera a triagem. Não há login. Se no futuro houver mais de um usuário, isso será outra spec.

### O que pode ir ao LLM

- textos mapeados como respostas de chatbot, quando presentes e utilizáveis
- critérios qualitativos do projeto
- o template de prompt da versão em uso
- identificador estável do candidato (`candidatoId`), para o modelo e o log correlacionarem a linha

### O que não vai ao LLM

- candidatos `inelegivel`
- candidatos `elegivel` sem resposta utilizável (ficam aguardando, sem chamada)
- campos que não participam do julgamento da etapa 2 (idade, escolaridade, último cargo, cidade, equipe, status legado, justificativa interna, nome)
- a planilha original completa

Idade, cargo e escolaridade já foram julgados na etapa 1. Não viajam de novo no payload da etapa 2.

### Nome

O nome **pode** aparecer no resultado local se o operador mapeou uma coluna de nome. **Não** vai no prompt. O prompt usa `candidatoId`. Não há coluna `Nome` confirmada em código vigente (só linha comentada em `model_ml.py`); portanto o contrato não a torna obrigatória.

### Segredo

`LLM_API_KEY` só em ambiente local, fora do Git. Sem chave, a etapa 2 não chama rede.

## Justificativa

O legado prova ausência de autenticação. O produto novo precisa de LLM só para quem já passou nos critérios duros e tem resposta. Identificador no prompt e nome só na tela local separam operação de exposição ao fornecedor.

## Consequência

- Agente 2 monta o payload com o mínimo acima; não “enriquece” o prompt com o restante da linha.
- Logs de token e de erro guardam `candidatoId` e `projetoId`, não o nome.
- Não especificar JWT, OAuth, RBAC nem auditoria corporativa nesta entrega.
