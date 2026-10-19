# PROMPT — AGENTE IMPLEMENTADOR DOS RANKINGS

Você implementa só `specs/revisao/03-rankings.md`. A job description e a análise por pergunta já estão no código. As notas já nascem na chamada e já são gravadas. Este agente calcula a média, zera a nota técnica quando falta informação, ordena o lote e mostra os três rankings.

## 1. Missão

No fim da avaliação por IA, cada pessoa com as duas notas entra em três ordenamentos: técnico, comportamental e final. A posição é do lote e o backend calcula na leitura. O modelo não manda ranking.

A triagem dura não muda. O botão **Avaliar trajetória** continua visível, desabilitado, e não dispara request.

## 2. Fontes, nesta ordem

Leia antes de alterar código:

1. `specs/revisao/03-rankings.md` — o que implementar. Critérios CA-R-01 a CA-R-08.
2. `specs/revisao/02-analise-por-pergunta.md` — schema que já existe. Não troque as chaves do JSON nem a montagem da pergunta.
3. `specs/history.md` — entrada de 2026-09-23.

Leia o código atual e estenda. Notas e `por_pergunta` já estão em `apps/api/avaliacao_ia/validacao.py`, `apps/api/avaliacao_ia/servico.py` e na tela `apps/web/src/pages/Resultado.tsx`. O Excel da triagem está em `apps/api/triagem/exportar.py`. Não o substitua.

## 3. Decisões já fechadas

Não escolha de novo.

- Escala de cada nota: inteiro de 0 a 100. 100 é o mais alto. Quem recebe nota: só `estado = sucesso` com schema válido.
- Quem entra no ranking: só quem tem as duas notas no lote atual. Inelegível, aguardando, pendente de IA, falha e avaliação do schema antigo ficam sem posição.
- `nota_final` é a média aritmética, arredondamento meio para cima: 0,5 sobe. Exemplos: 78 e 70 → 74; 78 e 71 → 75; 0 e 1 → 1; 0 e 0 → 0. Não use o `round` nativo do Python: ele arredonda 0,5 para o par e transformaria 74,5 em 74. A soma 0–200 fica rejeitada. Pesos iguais. Sem peso configurável.
- Se o modelo mandar `nota_final` ou `ranking`, isso já é chave extra do schema da spec 02: `falha_avaliacao`, sem nota persistida e sem posição. Não afrouxe essa validação.
- Posição calculada na leitura do resultado, não dentro do JSON da chamada. Ordem total: 1, 2, 3, sem pular e sem duas pessoas na mesma posição.
- Ranking técnico: `nota_tecnica` decrescente; empate por `nota_comportamental` decrescente; empate por `linhaOrigem` crescente.
- Ranking comportamental: `nota_comportamental` decrescente; empate por `nota_tecnica` decrescente; empate por `linhaOrigem` crescente.
- Ranking final: `nota_final` decrescente; empate por `nota_tecnica` decrescente; empate por `linhaOrigem` crescente.
- Sem nota, as três posições são nulas. A tela mostra “—”, não zero. Zero é nota. Ausência de ranking é outra coisa.
- Se toda pergunta da chamada é `sem_informacao`, grave `nota_tecnica = 0` mesmo que o modelo tenha mandado outro inteiro. `nota_comportamental` permanece a do modelo. `notaTecnicaZeradaPorFaltaDeInformacao = true` só nesse caso. A tela avisa que a nota técnica foi zerada por falta de informação para o cruzamento. Exemplo: modelo manda técnica 90 e comportamental 40, todas `sem_informacao` → técnica gravada 0, final 20.
- Fora esse zeramento, o backend não remapeia a faixa nem copia uma nota na outra. Resposta clara e fora do tema pode ter comportamental alta e técnica baixa.
- Avaliação antiga, só com `compatibilidade` e sem as duas notas, não entra no ranking e não ganha nota inventada.
- Reexecutar a IA de uma pessoa atualiza as notas dela. A leitura seguinte recalcula as posições do lote inteiro. Não congele posição no JSON antigo.
- Posição pode ser só derivada na leitura. Se gravar posição, é cache e tem de ser refeito quando qualquer nota do lote mudar. O aceite olha o valor calculado.
- A tela de resultado, no disparo novo, mostra nota técnica, nota comportamental, nota final e a posição no formato `2 de 15`, contando só quem tem nota. O padrão da ordenação é o ranking final, posição 1 no topo. Dá para ordenar por cada um dos três rankings e filtrar só quem tem nota, além dos filtros de estado que já existem.
- Não exiba `contratado`. Não use compatível, parcial ou incompatível no lugar destas três colunas no disparo novo. O schema antigo pode continuar mostrando o veredito antigo, sem nota inventada.
- Botão **Exportar resultado** na tela de resultado, arquivo diferente do Excel da triagem. Colunas, nesta ordem: `Linha`, `Nome`, `Busca LKD`, `Email`, `Telefone`, `Nota técnica`, `Ranking técnico`, `Nota comportamental`, `Ranking comportamental`, `Nota final`, `Ranking final`, `Perguntas`.
- `Perguntas` junta cada cabeçalho e o resultado, com os rótulos `atende`, `atende parcialmente`, `não atende`, `sem informação`. Sem nota, as células de nota e ranking ficam vazias. Nome e contato só se já estiverem no lote. Não vão ao LLM.
- O Excel da triagem (decisão dura e motivos) permanece o endpoint e as colunas que já existem.

## 4. O que construir

1. Calcular `nota_final` no backend e gravar, junto com a flag de zeramento. Aplicar o zeramento da nota técnica antes da média.
2. Na leitura do resultado, devolver as três notas e as três posições, com o denominador de quem tem nota.
3. Completar a tela de resultado: notas, posições `2 de 15`, aviso de zeramento, ordenação e filtro de quem tem nota.
4. Exportar o Excel da avaliação, sem alterar o Excel da triagem.
5. Testes automatizados CA-R-01 a CA-R-08.
6. Os testes já existentes de job description, gate de elegível e análise por pergunta continuam passando. Não afrouxe o schema: chave extra continua falha; trecho fora da resposta continua falha; inelegível continua sem chamada.

## 5. Fora desta implementação

- Pesos configuráveis, quarto ranking, inferência de personalidade.
- Refazer a tela de job description, o mapeamento da pergunta ou o template do prompt, fora o que o zeramento exigir no momento de gravar a nota.
- Trajetória, login, funil do legado, leitor de PDF.
- Reescrever spec, ADR ou contrato. Se um detalhe da spec 03 estiver impossível, pare nesse ponto, descreva o bloqueio e não invente outra regra.

## 6. Pronto quando

- CA-R-01 a CA-R-08 passam, e os CA-JD e CA-P já existentes continuam passando.
- 78 e 71 viram nota final 75, não 74.
- Três pessoas com técnica 80/40 na linha 2, 80/90 na linha 9 e 70/99 na linha 1 ficam, no ranking técnico, na ordem B, A, C, posições 1, 2 e 3.
- Inelegível no mesmo lote não entra no denominador.
- Todas as perguntas `sem_informacao` gravam técnica 0, final 20, e a tela avisa.
- Avaliação antiga não ganha nota nem posição.
- O Excel novo sai na tela de resultado. O Excel da triagem continua o de decisão e motivos.
- O navegador não chama o provedor. O botão Avaliar trajetória não chama a API.

Não declare a entrega pronta só com a tela estática. Rode os testes e uma leitura de resultado em que a posição muda depois de reavaliar uma pessoa.
