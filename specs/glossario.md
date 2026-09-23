# Glossário

Estes termos valem para todos os agentes. Não reutilizar o vocabulário enganoso do legado.

## Inelegível

Falhou pelo menos um critério duro **ativo** configurado na tela da etapa 1. Não é o antigo `fora do perfil`. Não é julgamento de LLM.

## Elegível na triagem

Passou em todos os critérios duros **ativos**. Ainda não é compatível com a vaga. Ainda não autoriza, sozinho, chamada ao LLM.

## Aguardando resposta

Elegível na triagem e **sem** resposta de chatbot utilizável. Sem chamada de API. Não é inelegível.

## Compatível / parcial / incompatível

Julgamento do LLM sobre a vaga, só na etapa 2. O agente 2 pode ajustar os três rótulos se documentar na spec dele. Não pode colapsar isso em `contratado`, `Sim`/`Nao` do modelo legado, nem em `Dentro do Perfil`.

## Último cargo

O cargo mais recente indicado pelo **mapeamento de colunas** na importação. É o texto mapeado, não a primeira palavra, não a taxonomia do legado, não `Cargo Anterior` por default (ADR 006).

## Projeto

A vaga ou o processo seletivo em avaliação, dono dos critérios duros, dos critérios qualitativos e do prompt. Um mapeamento importado pertence a um projeto.

## Critério duro (determinístico)

Regra de aceite/recusa executada sem LLM: cargos aceitos, faixa de idade, escolaridade, cada um com flag ativo/inativo. Detalhe da comparação: agente 1.

## Critério qualitativo

Critério da vaga usado só na avaliação por LLM. Distinto do critério duro. Detalhe: agente 2.

## Resposta de chatbot utilizável

Texto de resposta mapeado na importação, presente e não vazio após o critério de utilizável que o agente 2 definir. O legado só tinha status (`Enviado`, `Respondido`, `Elegível`); isso **não** substitui o texto.

## Prompt do projeto

Template editável na tela, com critérios qualitativos injetados, versionado. É o artefato que consome token. Detalhe: agente 2.

## Trajetória profissional

Função futura (etapa 3): perfil a partir de cargos, resumos e headlines. Identificador de ação `avaliar_trajetoria`. Fora da primeira entrega.

## Termos do legado que não se reutilizam como produto

| Termo legado | Por que não |
|---|---|
| `contratado` | Rótulo interno que junta ligar, standby, sem interesse, finalista, contratado real, etc. |
| `fora do perfil` | Lista hardcoded de reprovações + modelo ML; não é a triagem nova |
| `Taxa de Contratação` | Nome no Excel para a taxa de `contratado` interno |
| `ANÁLISE - INDICAÇÃO PERFIL BI - AI` | Saída Sim/Nao da regressão logística |
| `desconsiderar model ml` | Filtro de treino/predicao, não estado de produto |
| `Dentro do Perfil` | Contagem do funil sobre o rótulo `contratado` |
