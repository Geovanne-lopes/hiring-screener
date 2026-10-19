# PROMPT — CORREÇÃO: ESCOLARIDADE COM CONTAINS

A spec `specs/revisao/04-criterios-duros-cargo-empresa-idade.md` já foi implementada. Esta correção muda só a escolaridade. Não reabra cargo, empresa, idade, job description, análise por pergunta nem ranking.

## 1. Missão

A lista de escolaridade deixa de ser igualdade exata. A frase aceita entra se as palavras dela aparecem seguidas dentro da célula, no mesmo contains de cargo.

`Bacharelado` passa a aceitar `Bacharelado em Estatística`. `Ensino Superior` passa a aceitar um texto em que essas duas palavras apareçam seguidas, como `Ensino Superior Completo`.

## 2. Fontes

Leia o código já entregue da spec 04, em especial a comparação de cargo e a de escolaridade em `apps/api/triagem/avaliar.py`, e a tela de critérios.

O CA-CD-08 da spec 04 dizia que `Bacharelado em Estatística` continua fora de uma lista que só tem `Bacharelado`. Essa frase fica superada por este prompt. Não reescreva a spec 04.

## 3. Decisões já fechadas

Não escolha de novo.

- Reutilize a partição em palavras do cargo: acento e maiúscula fora, `/`, `|`, traço, vírgula e ponto-e-vírgula viram espaço, e a frase casa se as palavras aparecem seguidas e na mesma ordem.
- `Bacharelado` casa com `Bacharelado em Estatística` e com `Bacharelado - Estatística`.
- `Ensino Superior` casa com `Ensino Superior Completo` e com `Ensino Superior em Administração`.
- A frase aceita é que precisa caber na célula. `Bacharelado em Estatística` na lista não casa com uma célula que seja só `Bacharelado`.
- Sem gênero. `Bacharel` não vira `Bacharela` por esta correção.
- Sem `Sr`, `Pl`, `Jr`. Sem tradução para o inglês.
- Sem cortar na primeira palavra e sem reclassificar para `bacharelado` valor raro.
- Escolaridade vazia, com o bloco ativo, continua bloqueando o lote se a lista estiver vazia, e continua dado inválido se a célula estiver vazia.
- O valor original da célula continua gravado. O resultado mostra lido → palavras comparadas.
- Na tela de escolaridade, troque o texto de igualdade por: “A frase aceita entra se as palavras dela aparecerem seguidas na célula. Maiúsculas e acentos são ignorados. Não há abreviação automática nem tradução.”
- Escolaridade não vai ao LLM.

## 4. O que construir

1. Trocar só a comparação de escolaridade para esse contains.
2. Ajustar o texto fixo da tela.
3. Teste: lista com `Bacharelado` aceita `Bacharelado em Estatística`.
4. Teste: lista com `Ensino Superior` aceita `Ensino Superior Completo` e recusa `Superior incompleto`.
5. Testes de cargo, empresa, idade e do gate do LLM continuam passando. Não afrouxe o contains de cargo nem volte a igualdade de escolaridade.

## 5. Fora desta correção

- Mudar cargo, cargos bloqueados, empresas, idade, abreviações ou gênero.
- Tabela de inglês.
- Job description, prompt, rankings, trajetória.

## 6. Pronto quando

- `Bacharelado em Estatística` é elegível neste critério quando a lista tem `Bacharelado`.
- `Ensino Superior Completo` é elegível quando a lista tem `Ensino Superior`.
- `Superior incompleto` não é elegível para essa mesma lista.
- Nenhuma chamada de LLM. Cargo, empresa e idade permanecem como a spec 04 deixou.
