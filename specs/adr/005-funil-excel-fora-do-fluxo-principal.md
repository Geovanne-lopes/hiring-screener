# ADR 005 — Destino do funil Excel do legado

## Status

Aceita.

## Problema

`data_vis_carrefour.py` gera `Analise [RENOMEAR].xlsx` com taxas por coluna (Enviado/Respondeu/Elegível ou Candidatos/Dentro do Perfil/Taxa de Contratação). A operação nova continua triando um mapeamento contra uma vaga, com resultado por pessoa. Não está decidido se o Excel de funil entra na primeira entrega.

## Impacto

Se o funil for o fluxo principal, a tela vira um gerador de Excel e a triagem determinística + LLM ficam secundárias. Se for obrigatório na primeira entrega, compete com o recorte de critérios editáveis e avaliação por respostas.

## Alternativas

1. Reproduzir o Excel de funil como entrega principal. Rejeitada: “fazer a mesma coisa” não significa reproduzir esse relatório nem o rótulo `contratado`.
2. Incluir o funil como relatório obrigatório da primeira entrega. Não bloqueia o produto novo, mas desloca esforço da regra editável.
3. Fora do fluxo principal e fora do escopo de implementação da primeira entrega. Pode voltar depois como relatório opcional.

## Decisão

O relatório de funil do script antigo **não entra na primeira entrega** e **não é o fluxo principal**.

O resultado principal passa a ser, por candidato:

- motivo(s) de inelegibilidade, ou
- perfil + compatibilidade (quando a etapa 2 rodou), ou
- elegível aguardando resposta de chatbot.

O `--dev_mode` não é produto. O rótulo interno `contratado` não é produto.

## Justificativa

Não houve evidência nova no código de que o Excel de funil seja a operação a recuperar. O código confirma que ele agrupa status e não lê texto de respostas. A primeira entrega existe para devolver à operação o controle da regra de aceite/recusa e, depois, o julgamento qualitativo da vaga.

## Consequência

- Agentes 1 e 2 não especificam abas de funil, taxas por cidade/cargo nem export “Analise [RENOMEAR]”.
- Exportar um CSV/Excel **do resultado por candidato** (id, decisão, motivos, perfil, compatibilidade, versão do prompt) é permitido como apoio operacional; não é o funil legado.
- Se a operação pedir o funil depois, isso é spec nova, opcional, sem alterar os contratos de `DecisaoTriagem` e `AvaliacaoIa`.
