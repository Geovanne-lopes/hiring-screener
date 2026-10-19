# Revisão — Rankings técnico, comportamental e final

Spec do ordenamento no fim da avaliação por IA. As notas nascem na mesma chamada definida em `specs/revisao/02-analise-por-pergunta.md`. As **posições** são calculadas no backend, sobre o lote, e não vêm do modelo.

Três ordenamentos:

| Ranking | Base |
|---|---|
| Técnico | Cruzamento das respostas com as perguntas (cabeçalhos) e com a job description |
| Comportamental | A escrita do candidato nas respostas enviadas. É o critério comportamental desta revisão. Não há segunda lista de critérios |
| Final | Média aritmética das duas notas |

Esta spec não reabre a triagem dura e não habilita trajetória.

---

## 1. Decisões fechadas

| Tema | Decisão |
|---|---|
| Escala | Inteiro de 0 a 100, inclusive, em cada nota. 100 é o mais alto |
| Quem recebe nota | Só avaliação com `estado = sucesso` e schema válido |
| Quem entra no ranking | Só quem tem as duas notas persistidas no lote atual. Inelegível, aguardando, pendente de IA e falha ficam sem posição |
| Técnico | `nota_tecnica`: o quanto as respostas, lidas contra as próprias perguntas, se aproximam do que a job description descreve |
| Comportamental | `nota_comportamental`: clareza, organização, coerência e adequação do texto a uma resposta profissional. Uma nota só, não quatro |
| Final | `nota_final = arredondamento meio para cima de (nota_tecnica + nota_comportamental) / 2`, inteiro de 0 a 100 |
| Posição | Ordem total, calculada na leitura do resultado. O modelo não envia rank. Empate de nota não divide posição: o desempate abaixo produz 1, 2, 3, … |
| Soma | Rejeitada como nota final. A soma ficaria em 0–200 e não se compara com as notas parciais |
| União | Rejeitada. Não produz um número ordenável |
| Média | Adotada |
| Peso | Iguais. Não há peso configurável nesta revisão |
| Escrita | Não é teste de personalidade, não é “fit cultural” e não infere traço que o texto não mostre. Ortografia sozinha não esgota a nota: entram clareza e organização |
| Todas as perguntas `sem_informacao` | O backend grava `nota_tecnica = 0`, mesmo que o modelo tenha mandado outro inteiro. A nota comportamental permanece a do modelo, se estiver em 0–100. A tela avisa que a nota técnica foi zerada por falta de informação para o cruzamento |

---

## 2. O que cada nota olha

### 2.1 Ranking técnico

Olha o conteúdo: a resposta responde à pergunta da coluna e esse conteúdo conversa com a job description.

Não olha cargo, idade nem escolaridade. Não aumenta a nota porque a job description é longa. Não cita a job description como fala do candidato.

Rubrica enviada no template (secção 5.4 da spec 02) e repetida aqui para o cálculo não mudar de significado:

| Faixa | Leitura |
|---|---|
| 0–20 | A resposta não trata da pergunta, ou não há informação para cruzar com a vaga |
| 21–40 | Encosta no tema da pergunta com pouca relação com a job description |
| 41–60 | Responde parte da pergunta e parte do que a vaga descreve |
| 61–80 | Responde a pergunta e cobre o que a job description pede nesse tema, com lacuna pontual |
| 81–100 | A resposta sustenta a pergunta e o que a job description pede nesse tema, sem fato inventado |

O modelo escolhe o inteiro. O backend não remapeia a faixa, exceto o zeramento da secção 1 quando toda pergunta veio `sem_informacao`.

### 2.2 Ranking comportamental

Olha **como** está escrito o conjunto das respostas enviadas daquela pessoa. Uma nota para o candidato, não uma nota por coluna.

Conta:

- clareza: dá para entender o que a pessoa afirma;
- organização: as ideias vêm numa sequência que se acompanha;
- coerência: as frases não se contradizem entre si;
- adequação: o texto funciona como resposta profissional, não como resto de frase ou cópia ilegível.

Não conta como eixo separado: simpatia inferida, “proatividade” sem exemplo na escrita, idade, cargo, escolaridade, nome.

| Faixa | Leitura |
|---|---|
| 0–20 | Texto vazio de sentido, ilegível ou só fragmentos sem frase |
| 21–40 | Dá para extrair uma ideia, com quebra frequente de clareza ou organização |
| 41–60 | Texto compreensível, com trechos confusos ou pouco organizados |
| 61–80 | Escrita clara e organizada, com deslize pontual |
| 81–100 | Escrita clara, organizada e coerente ao longo das respostas enviadas |

Resposta curta porém clara pode ter nota comportamental alta e nota técnica baixa. Os dois eixos não se copiam.

### 2.3 Ranking final

`nota_final` é a média aritmética, meio para cima (0,5 sobe). Exemplos: 78 e 70 → 74; 78 e 71 → 75; 0 e 1 → 1; 0 e 0 → 0.

O backend calcula. Se o modelo mandar uma chave `nota_final` ou `ranking`, isso é chave extra: `falha_avaliacao` (schema da spec 02). A posição não é confiada ao modelo porque depende das outras pessoas do lote.

---

## 3. Como a posição é calculada

Na leitura do resultado do projeto, sobre as avaliações de sucesso do lote atual.

Ordem do **ranking técnico**: `nota_tecnica` decrescente; empate por `nota_comportamental` decrescente; empate por `linhaOrigem` crescente.

Ordem do **ranking comportamental**: `nota_comportamental` decrescente; empate por `nota_tecnica` decrescente; empate por `linhaOrigem` crescente.

Ordem do **ranking final**: `nota_final` decrescente; empate por `nota_tecnica` decrescente; empate por `linhaOrigem` crescente.

A posição é 1 para o primeiro dessa ordem, 2 para o seguinte, sem pular número. Dois candidatos não ficam na mesma posição.

Quem não tem nota: os três campos de posição vão nulos. A tela mostra “—”, não zero. Zero de nota é nota; ausência de ranking é outra coisa.

Reexecutar a IA de uma pessoa atualiza as notas dela. As posições de todo o lote são recalculadas na próxima leitura. Não se congela a posição dentro do JSON antigo.

Avaliação antiga (schema com `compatibilidade` e sem as duas notas) não entra nestes rankings. Não se inventa nota para ela.

---

## 4. Persistência

Em `AvaliacaoIa` de disparo novo, quando `estado = sucesso`:

| Campo | Origem |
|---|---|
| `notaTecnica` | modelo, ou `0` se toda pergunta é `sem_informacao` |
| `notaComportamental` | modelo |
| `notaFinal` | backend, secção 2.3 |
| `notaTecnicaZeradaPorFaltaDeInformacao` | `true` só nesse zeramento |

Posições **não** são colunas obrigatórias: derivam na leitura. Se a implementação gravar posição, ela é cache descartável e tem de ser refeita quando qualquer nota do lote mudar. A spec de aceite olha o valor calculado, não um cache velho.

`usoToken` e `promptVersionId` continuam como na etapa 2. Acrescenta-se `jobDescriptionVersaoId` da versão embutida naquele prompt.

---

## 5. Tela de resultado

Além do que a spec 02 mostra por pergunta:

- nota técnica, nota comportamental, nota final;
- posição em cada ranking, no formato `2 de 15` entre quem tem nota;
- aviso quando a nota técnica foi zerada por falta de informação.

Filtros novos, somados aos já existentes de estado da triagem:

- ordenar pela posição técnica, pela comportamental ou pela final (padrão da tela: ranking final, posição 1 no topo);
- ver só quem tem nota.

Não exibir `contratado`. Não usar compatível/parcial/incompatível como substituto destas três colunas.

### 5.1 Exportar resultado

Botão na tela de resultado, distinto do Excel da triagem determinística. Planilha com uma linha por candidato do lote, nesta ordem de colunas:

`Linha`, `Nome`, `Busca LKD`, `Email`, `Telefone`, `Nota técnica`, `Ranking técnico`, `Nota comportamental`, `Ranking comportamental`, `Nota final`, `Ranking final`, `Perguntas`.

`Perguntas` junta, em um texto, cada cabeçalho e o resultado (`atende`, `atende parcialmente`, `não atende`, `sem informação`). Sem nota, as células de nota e ranking ficam vazias. Nome e contato só se já estiverem no lote importado; não vão ao LLM.

O Excel da triagem (decisão dura, motivos) permanece o que já existe. Este arquivo é o da avaliação.

---

## 6. Critérios de aceite

### CA-R-01 — Média

Given notas persistidas 78 e 70  
When o resultado é lido  
Then `nota_final` é 74

Given 78 e 71  
Then `nota_final` é 75

### CA-R-02 — Posição não vem do modelo

Given JSON válido com as duas notas e uma chave `ranking`  
When o backend valida  
Then `falha_avaliacao`  
And essa pessoa não ganha posição

### CA-R-03 — Ordem técnica com desempate

Given A com técnica 80 e comportamental 40, linha 2  
And B com técnica 80 e comportamental 90, linha 9  
And C com técnica 70 e comportamental 99, linha 1  
When o ranking técnico é lido  
Then a ordem é B, A, C  
And as posições são 1, 2 e 3

### CA-R-04 — Inelegível fora

Given um inelegível no mesmo lote de dois avaliados com sucesso  
When o ranking final é lido  
Then o inelegível não tem posição  
And o denominador é 2

### CA-R-05 — Zeramento técnico

Given todas as perguntas da chamada com `sem_informacao` e `nota_tecnica` 90 no JSON, `nota_comportamental` 40, schema válido no restante  
When persiste  
Then `nota_tecnica` gravada é 0  
And `nota_final` é 20  
And a tela avisa o zeramento

### CA-R-06 — Eixos independentes

Given uma resposta curta, clara e fora do tema da pergunta e da job description  
When a chamada retorna schema válido  
Then é permitido `nota_comportamental` alta com `nota_tecnica` baixa  
And o backend não copia uma nota na outra

### CA-R-07 — Reexecução recalcula o lote

Given A na posição final 1 e B na 2  
When uma nova avaliação de B fica com `nota_final` maior que a de A  
Then a leitura seguinte mostra B na posição 1 e A na 2

### CA-R-08 — Avaliação antiga

Given uma avaliação só com `compatibilidade` e sem as duas notas  
When os rankings são lidos  
Then essa linha não recebe posição nem nota inventada

---

## 7. Fora desta spec

- Pesos configuráveis por vaga
- Quarto ranking
- Inferência de personalidade além da escrita
- Trajetória profissional
- PDF de job description
