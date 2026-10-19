# Revisão — Justificativa da nota técnica e da nota comportamental

Spec da explicação de cada nota. O `perfil` continua sendo o resumo geral. As duas justificativas novas explicam o inteiro de cada eixo.

As notas, a média e as posições continuam as de `specs/revisao/03-rankings.md`. O julgamento por pergunta continua o de `specs/revisao/02-analise-por-pergunta.md`. Esta spec não reescreve esses arquivos. No disparo novo, prevalece este arquivo nas chaves do JSON, no texto pedido ao modelo e nas colunas do Excel do resultado (`specs/history.md`).

Uma HTTP por candidato. O modelo não devolve posição no lote.

---

## 1. Decisões fechadas

| Tema | Decisão |
|---|---|
| Resumo | Continua sendo `perfil`: um parágrafo curto sobre o que as respostas sustentam à luz da job description. Não é a explicação da nota |
| Nota técnica | Inteiro `nota_tecnica`, como na spec 03. Ao lado, `justificativa_nota_tecnica`: por que esse inteiro, lido contra a rubrica técnica |
| Nota comportamental | Inteiro `nota_comportamental`, como na spec 03. Ao lado, `justificativa_nota_comportamental`: por que esse inteiro, lido contra a rubrica da escrita |
| Obrigatoriedade | Nos dois campos, string não vazia depois de strip. Ausência, tipo errado ou só whitespace falha o schema |
| Chaves da raiz | Exatamente sete: `perfil`, `por_pergunta`, `trechos`, `nota_tecnica`, `nota_comportamental`, `justificativa_nota_tecnica`, `justificativa_nota_comportamental`. Chave extra na raiz continua falha |
| Itens de pergunta e trecho | Iguais à spec 02. Chave extra dentro do item continua ignorada. Chave obrigatória do item ausente continua falha |
| Avaliação já gravada | Permanece válida. Sem os dois textos, a tela e o Excel deixam essas células vazias. Não se inventa justificativa na leitura |
| Zeramento técnico | Se todas as perguntas vieram `sem_informacao`, o backend grava `nota_tecnica = 0`, como na spec 03, e substitui `justificativa_nota_tecnica` pela frase fixa da secção 4. A justificativa comportamental gravada é a do modelo |
| Prompt já salvo | Não bloqueia o disparo e não exige salvar de novo. Não desalinha a job description. O bloco de formato do sistema e o parágrafo fixo da secção 3 vão em toda chamada |
| Nota final | Continua a média meio para cima. Não há justificativa própria da nota final |
| Ranking | Continua calculado no backend. O modelo não envia posição |

---

## 2. O que cada texto diz

### 2.1 Resumo (`perfil`)

Igual à spec 02. Parágrafo curto, no máximo cinco frases, só com o que as respostas sustentam à luz da job description. Não explica a faixa da nota.

### 2.2 Justificativa da nota técnica

Um parágrafo, no máximo três frases. Diz por que o inteiro cabe na faixa da rubrica técnica da spec 03 (secção 2.1): o quanto as respostas, cruzadas com as perguntas, se aproximam do que a job description pede.

Cita o que a resposta traz e o que falta. Não trata trecho da job description como fala do candidato. Não julga cargo, idade, escolaridade nem empresa. Não repete o resumo no lugar da explicação da nota.

### 2.3 Justificativa da nota comportamental

Um parágrafo, no máximo três frases. Diz por que o inteiro cabe na faixa da rubrica comportamental da spec 03 (secção 2.2): clareza, organização, coerência e adequação do texto.

Não infere simpatia, proatividade sem exemplo na escrita, idade, cargo, escolaridade nem nome. Pode divergir da nota técnica: resposta curta e clara pode ter justificativa comportamental alta e justificativa técnica baixa.

O backend não compara o texto com o resumo nem mede número de frases. Exige string não vazia depois de strip. O limite de frases vai na instrução ao modelo.

---

## 3. Prompt

`INSTRUCOES_TECNICAS` passa a listar as sete chaves e a exigir os dois parágrafos, cada um com no máximo três frases, apontando a faixa da rubrica correspondente. Continua a mensagem de sistema de toda chamada.

`TEMPLATE_INICIAL` ganha dois passos na tarefa, depois das notas:

- `justificativa_nota_tecnica`: por que a nota técnica está naquela faixa;
- `justificativa_nota_comportamental`: por que a nota comportamental está naquela faixa.

O passo do `perfil` permanece o resumo, sem pedir que ele explique as notas.

Em toda chamada, depois do template salvo, o backend acrescenta este parágrafo, mesmo que o texto salvo ainda liste só as cinco chaves antigas:

> A lista de chaves das instruções técnicas prevalece. Inclua justificativa_nota_tecnica e justificativa_nota_comportamental. Cada uma é um parágrafo de no máximo três frases que explica o inteiro daquela nota. perfil continua sendo só o resumo.

Pré-visualizar mostra esse parágrafo. Pré-visualizar não chama o modelo.

---

## 4. JSON de saída

Chaves exatas da raiz:

`perfil`, `por_pergunta`, `trechos`, `nota_tecnica`, `nota_comportamental`, `justificativa_nota_tecnica`, `justificativa_nota_comportamental`.

| Campo | Regra |
|---|---|
| `justificativa_nota_tecnica` | string não vazia depois de strip |
| `justificativa_nota_comportamental` | string não vazia depois de strip |

O restante do objeto segue a spec 02 e a spec 03, inclusive o zeramento de `nota_tecnica` quando toda pergunta é `sem_informacao`.

Quando esse zeramento ocorre, o backend grava em `justificativa_nota_tecnica` exatamente:

`A nota técnica foi zerada porque nenhuma resposta trouxe informação para cruzar com a pergunta e a job description.`

O texto que o modelo enviou para essa chave não é gravado nesse caso. `justificativa_nota_comportamental` permanece a do modelo.

Falha de schema, incluindo as duas justificativas ausentes ou vazias: uma tentativa de reparo. A mensagem específica da validação vai para o modelo, como já ocorre no reparo. Se o reparo também falhar, `falha_avaliacao`, sem perfil inventado, sem nota persistida, sem as duas justificativas, sem ranking. `DecisaoTriagem` intacta.

Exemplo mínimo, com uma pergunta:

```json
{
  "perfil": "A resposta descreve escuta e ajuste de abordagem no atendimento, em linha com o que a vaga pede na job description.",
  "por_pergunta": [
    {
      "perguntaId": "p1",
      "pergunta": "Como você identifica as necessidades do cliente e personaliza sua abordagem para o atendimento?",
      "resultado": "atende",
      "justificativa": "A resposta conta como pergunta o contexto do cliente e muda a explicação. Isso conversa com a pergunta e com o atendimento descrito na job description."
    }
  ],
  "trechos": [
    {
      "perguntaId": "p1",
      "trecho": "eu pergunto o que a pessoa já tentou e explico de outro jeito"
    }
  ],
  "nota_tecnica": 78,
  "nota_comportamental": 70,
  "justificativa_nota_tecnica": "A resposta trata a pergunta e cobre o atendimento descrito na vaga, com lacuna pontual. Isso cabe na faixa 61–80.",
  "justificativa_nota_comportamental": "O texto é claro e segue uma sequência. Há um deslize pontual de organização, o que cabe na faixa 61–80."
}
```

---

## 5. Persistência e API

Colunas novas em `avaliacoes_ia`, texto, anuláveis:

- `justificativa_nota_tecnica`
- `justificativa_nota_comportamental`

Avaliação antiga, sem essas colunas preenchidas, continua legível. A migração não preenche texto.

No JSON público da avaliação com sucesso e schema novo:

| Campo | Origem |
|---|---|
| `justificativaNotaTecnica` | coluna técnica; `null` se a avaliação antiga não tiver o texto |
| `justificativaNotaComportamental` | coluna comportamental; `null` se a avaliação antiga não tiver o texto |

`perfil` continua o resumo. Falha de avaliação não grava os dois textos.

---

## 6. Tela de resultado

Na linha avaliada com sucesso e schema novo, rótulos visíveis:

- **Resumo**, antes do parágrafo de `perfil`;
- **Justificativa da nota técnica**, junto da nota técnica;
- **Justificativa da nota comportamental**, junto da nota comportamental.

Avaliação antiga sem os textos mostra as notas e o resumo, e omite os dois parágrafos. O aviso de zeramento técnico da spec 03 permanece.

A justificativa de cada pergunta continua debaixo do cabeçalho da coluna. Não usa o mesmo rótulo das notas.

---

## 7. Excel do resultado

O arquivo continua o da avaliação, distinto do Excel da triagem. A opção **Só quem tem nota** continua valendo: marcada, só entram linhas com posição final; desmarcada, o lote inteiro.

Ordem das colunas:

`Linha`, `Nome`, `Email`, `Telefone`, `Nota técnica`, `Justificativa da nota técnica`, `Ranking técnico`, `Nota comportamental`, `Justificativa da nota comportamental`, `Ranking comportamental`, `Nota final`, `Ranking final`, `Perguntas`, `Resumo`, e em seguida uma coluna `Justificativa pergunta 1`, `Justificativa pergunta 2`, … na ordem das perguntas do lote.

`Busca LKD` não volta. O Excel da triagem também permanece sem essa coluna.

Sem nota, as células de nota, ranking, resumo e justificativas ficam vazias. Avaliação antiga com nota e sem as duas justificativas de nota exporta essas duas células vazias e mantém resumo e notas.

`Perguntas` continua o texto único com cabeçalho e resultado. Cada `Justificativa pergunta N` leva só o texto da justificativa daquela pergunta.

---

## 8. Critérios de aceite

### CA-JN-01 — Dois textos distintos do resumo

Given JSON válido com `perfil`, as duas notas e as duas justificativas de nota  
When a avaliação persiste  
Then a tela mostra **Resumo** com o `perfil`  
And mostra **Justificativa da nota técnica** com o texto técnico  
And mostra **Justificativa da nota comportamental** com o texto comportamental

### CA-JN-02 — Justificativa ausente

Given JSON com as cinco chaves antigas e sem `justificativa_nota_tecnica`  
When o backend valida  
Then a mensagem de validação cita `justificativa_nota_tecnica`  
And o reparo recebe essa mensagem  
And, se o reparo também não trouxer a chave, o estado é `falha_avaliacao`  
And não há nota nem justificativa gravada

### CA-JN-03 — String vazia

Given `justificativa_nota_comportamental` igual a `"   "` e o restante válido  
When o backend valida  
Then falha de schema  
And a mensagem cita `justificativa_nota_comportamental`

### CA-JN-04 — Chave extra na raiz

Given JSON válido mais a chave `ranking`  
When o backend valida  
Then `falha_avaliacao` depois do reparo, se o reparo mantiver a chave extra  
And essa pessoa não ganha posição

### CA-JN-05 — Zeramento técnico troca a justificativa

Given todas as perguntas com `sem_informacao`, `nota_tecnica` 90, `nota_comportamental` 40 e as duas justificativas preenchidas  
When persiste  
Then `nota_tecnica` gravada é 0  
And `justificativa_nota_tecnica` gravada é a frase fixa da secção 4  
And `justificativa_nota_comportamental` gravada é a do modelo  
And `nota_final` é 20

### CA-JN-06 — Avaliação antiga

Given uma avaliação com as duas notas e `perfil`, sem as duas colunas de justificativa de nota  
When o resultado é lido e exportado  
Then a linha mantém notas, ranking e resumo  
And as células **Justificativa da nota técnica** e **Justificativa da nota comportamental** ficam vazias  
And a tela não inventa parágrafo

### CA-JN-07 — Colunas do Excel

Given um lote com três perguntas e uma pessoa com nota  
When o resultado é exportado  
Then o cabeçalho contém, nesta ordem, `Nota técnica`, `Justificativa da nota técnica`, `Ranking técnico`, `Nota comportamental`, `Justificativa da nota comportamental`  
And depois de `Resumo` vêm `Justificativa pergunta 1`, `Justificativa pergunta 2` e `Justificativa pergunta 3`  
And o cabeçalho não contém `Busca LKD`

### CA-JN-08 — Prompt já salvo

Given um prompt salvo que ainda lista só as cinco chaves antigas e uma job description alinhada a esse prompt  
When o operador dispara a avaliação sem salvar o prompt de novo  
Then a chamada segue  
And a pré-visualização contém o parágrafo da secção 3  
And um JSON com as sete chaves válidas persiste

### CA-JN-09 — Só quem tem nota

Given o lote com uma pessoa com nota e outra sem nota  
When o Excel é exportado com **Só quem tem nota** marcado  
Then a planilha traz só a pessoa com posição final  
And as duas colunas de justificativa de nota estão presentes

---

## 9. Fora desta spec

- Justificativa própria da nota final
- Conferência automática de que o parágrafo não copia o resumo
- Corte do texto por número de frases no backend
- Reabrir cargo, empresa, idade ou escolaridade
- Trajetória profissional
- Devolver `Busca LKD` a qualquer Excel
