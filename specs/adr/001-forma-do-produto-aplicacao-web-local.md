# ADR 001 — Forma do produto: aplicação web local

## Status

Aceita.

## Problema

O legado é um script de terminal (`data_vis_carrefour.py` e `model_ml.py`). A operação precisa cadastrar critérios duros, critérios qualitativos e o prompt enviado ao LLM sem alterar código. Terminal não atende esse uso.

## Impacto

Sem tela, a regra de triagem continua no código e o produto não recupera o controle operacional. A escolha da forma do produto trava a stack, o empacotamento e o que os agentes de etapa podem assumir como interface.

## Alternativas

1. Continuar no terminal, com arquivos de configuração. Barato, mas a edição de prompt e critérios exige mexer em texto fora de um fluxo guiado. Rejeitada: o requisito é tela.
2. Aplicativo desktop nativo (Qt, Electron, Tauri). Tem tela e pode rodar offline, mas aumenta empacotamento e desvia o implementador para shell nativo sem ganho para um operador que já usa navegador e planilha.
3. Aplicação web multi-usuário em nuvem. Exige autenticação, hospedagem e papéis. O legado não tem nenhum desses. Fora de escopo.
4. Aplicação web local: o operador sobe o sistema na própria máquina e usa o navegador em `localhost`. Tem tela, não exige conta e persiste em arquivo local.

## Decisão

O produto da primeira entrega é uma **aplicação web local**. O terminal deixa de ser a interface da operação. Não há autenticação, papéis nem deploy corporativo nesta entrega.

## Justificativa

Quem opera precisa editar critérios e o prompt em tela. O navegador já está no ambiente de trabalho. Uma web app local entrega isso sem inventar usuários, JWT ou infraestrutura que o legado nunca teve.

## Consequência

- Os agentes de etapa especificam telas e fluxos de navegação, não CLI.
- A API escuta em localhost. Não há login.
- Se no futuro houver mais de um usuário, isso será outra spec. Ver ADR 007.
