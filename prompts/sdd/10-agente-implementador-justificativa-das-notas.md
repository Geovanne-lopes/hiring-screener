# PROMPT — AGENTE IMPLEMENTADOR DA JUSTIFICATIVA DAS NOTAS

Você implementa só `specs/revisao/05-justificativa-das-notas.md`. A job description, a análise por pergunta, os rankings e o Excel atual do resultado já estão no código. Este agente faz a IA devolver a justificativa da nota técnica e a justificativa da nota comportamental, mostra as duas na tela e as coloca no Excel.

## 1. Missão

O `perfil` continua sendo o resumo. Cada nota ganha um parágrafo próprio que explica o inteiro. Avaliação nova só persiste com os dois textos. Avaliação já gravada continua válida e exporta essas células vazias.

O botão **Avaliar trajetória** continua visível, desabilitado, e não dispara request.

## 2. Fontes, nesta ordem

Leia antes de alterar código:

1. `specs/revisao/05-justificativa-das-notas.md` — o que implementar. Critérios CA-JN-01 a CA-JN-09.
2. `specs/history.md` — entrada de 2026-09-24. Onde divergir das specs 02 e 03, vale a spec 05. Não reescreva essas specs.
3. `apps/api/avaliacao_ia/validacao.py`, `prompt.py`, `servico.py`, `exportar.py` e `apps/web/src/pages/Resultado.tsx` — o contrato e a tela que você estende.

Não reabra cargo, empresa, idade nem escolaridade.

## 3. Decisões já fechadas

Não escolha de novo.

- Chaves exatas da raiz, nesta avaliação nova: `perfil`, `por_pergunta`, `trechos`, `nota_tecnica`, `nota_comportamental`, `justificativa_nota_tecnica`, `justificativa_nota_comportamental`. Chave extra na raiz continua falha. Chave extra dentro do item de pergunta ou de trecho continua ignorada. Chave obrigatória do item ausente continua falha.
- `justificativa_nota_tecnica` e `justificativa_nota_comportamental` são strings não vazias depois de strip. Ausência, tipo errado ou só whitespace falha. A mensagem de validação cita o nome da chave que faltou ou veio vazia.
- O reparo de JSON continua sendo uma tentativa. A mensagem específica da validação vai para o modelo. Se o reparo também falhar, `falha_avaliacao`, sem perfil, sem nota, sem as duas justificativas e sem ranking. `DecisaoTriagem` intacta.
- `perfil` não passa a explicar a nota. Continua o parágrafo curto do resumo.
- Cada justificativa de nota é um parágrafo de no máximo três frases, na instrução ao modelo. O backend não conta frases e não compara o texto com o resumo.
- A justificativa técnica explica a faixa da rubrica técnica da spec 03. A comportamental explica a faixa da escrita. Os eixos não se copiam.
- Se todas as perguntas vieram `sem_informacao`, grave `nota_tecnica = 0` como já ocorre e substitua `justificativa_nota_tecnica` por exatamente: `A nota técnica foi zerada porque nenhuma resposta trouxe informação para cruzar com a pergunta e a job description.` A justificativa comportamental gravada é a do modelo. `nota_final` continua a média meio para cima.
- Não há justificativa da nota final. O modelo não envia posição.
- Colunas novas em `avaliacoes_ia`, texto, anuláveis: `justificativa_nota_tecnica` e `justificativa_nota_comportamental`. Avaliação antiga fica com essas colunas nulas. A leitura não inventa texto.
- No JSON público: `justificativaNotaTecnica` e `justificativaNotaComportamental`. `null` quando a avaliação antiga não tiver o texto.
- `INSTRUCOES_TECNICAS` lista as sete chaves e exige os dois parágrafos. `TEMPLATE_INICIAL` ganha os dois passos da secção 3 da spec, sem mudar o passo do `perfil`.
- Prompt já salvo não bloqueia o disparo, não exige salvar de novo e não desalinha a job description. Depois do template, toda chamada e toda pré-visualização acrescentam o parágrafo fixo da secção 3 da spec. Pré-visualizar não chama o modelo.
- Na tela, rótulos visíveis: **Resumo**, **Justificativa da nota técnica**, **Justificativa da nota comportamental**. A justificativa de cada pergunta continua debaixo do cabeçalho da coluna, com outro rótulo. Avaliação antiga sem os textos mostra notas e resumo e omite os dois parágrafos. O aviso de zeramento técnico permanece.
- Excel do resultado, nesta ordem: `Linha`, `Nome`, `Email`, `Telefone`, `Nota técnica`, `Justificativa da nota técnica`, `Ranking técnico`, `Nota comportamental`, `Justificativa da nota comportamental`, `Ranking comportamental`, `Nota final`, `Ranking final`, `Perguntas`, `Resumo`, `Justificativa pergunta 1`, `Justificativa pergunta 2`, … Sem nota, essas células ficam vazias. Avaliação com nota e sem as duas justificativas de nota exporta só essas duas células vazias.
- **Só quem tem nota** continua filtrando a exportação por posição final. `Busca LKD` não volta no Excel do resultado nem no da triagem.
- Nome, telefone, e-mail, cargo, idade, escolaridade e empresa continuam fora do payload do LLM.

## 4. O que construir

1. Validar e gravar as duas justificativas. No zeramento técnico, gravar a frase fixa no lugar do texto do modelo.
2. Atualizar as instruções técnicas, o template inicial e o parágrafo acrescentado depois do prompt salvo.
3. Expor os dois campos na API e na tela de resultado, com os rótulos da secção 6 da spec.
4. Inserir as duas colunas no Excel do resultado, na ordem da secção 7. Não desfazer `Resumo`, `Justificativa pergunta N`, o filtro **Só quem tem nota** nem a ausência de `Busca LKD`.
5. Testes CA-JN-01 a CA-JN-09. Testes antigos de schema que exigem só as cinco chaves passam a exigir as sete no disparo novo. Avaliação antiga sem as colunas continua sem nota inventada e sem texto inventado.

## 5. Fora desta implementação

- Justificativa da nota final, corte por número de frases, ou recusa porque o parágrafo copiou o resumo.
- Exigir que o operador salve o prompt de novo.
- Mudar triagem dura, job description, análise por pergunta além das chaves novas, média ou desempate de ranking.
- Trajetória, login, funil do legado.
- Reescrever spec ou ADR. Se um detalhe da spec 05 estiver impossível, pare nesse ponto, descreva o bloqueio e não invente outra regra.

## 6. Pronto quando

- CA-JN-01 a CA-JN-09 passam.
- JSON sem `justificativa_nota_tecnica` falha e a mensagem cita essa chave. JSON com as sete chaves válidas persiste.
- Todas as perguntas `sem_informacao` gravam nota técnica 0 e a frase fixa na justificativa técnica. A justificativa comportamental do modelo permanece.
- Uma avaliação antiga com nota e sem as duas colunas exporta essas células vazias e mantém o resumo.
- O Excel não contém `Busca LKD`. Com três perguntas, o cabeçalho tem `Justificativa da nota técnica`, `Justificativa da nota comportamental` e `Justificativa pergunta 1` a `3`.
- Prompt salvo com a lista antiga de cinco chaves ainda dispara, e a pré-visualização mostra o parágrafo da secção 3.
- O botão Avaliar trajetória não chama a API.

Não declare a entrega pronta só com a tela estática. Rode os testes e confira na tela de resultado os três rótulos: Resumo, Justificativa da nota técnica e Justificativa da nota comportamental.
