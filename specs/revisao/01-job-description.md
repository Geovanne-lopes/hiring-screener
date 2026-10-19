# Revisão — Job description da vaga

Spec da descrição geral da vaga. Encaixa uma etapa nova **depois dos critérios duros e antes da importação**. O texto salvo é uma variável do prompt da avaliação por IA.

Esta spec **não** altera cargo, idade nem escolaridade. **Não** habilita trajetória. **Não** reescreve `specs/sprint-1/avaliacao-ia-chatbot.md`: onde as duas divergirem, vale este arquivo e `specs/revisao/02-analise-por-pergunta.md`, com o conflito em `specs/history.md`.

Dono: revisão pedida pela operação em 2026-09-23.

---

## 1. Decisões fechadas

| Tema | Decisão |
|---|---|
| Lugar no fluxo | Passo próprio, logo depois dos critérios duros. Antes de importar, triar e avaliar |
| O que é | Texto da descrição geral da vaga daquele projeto. Contexto para a IA julgar respostas. Não é critério duro |
| Como entra | Colar no editor **ou** enviar arquivo `.txt`, `.md` ou `.docx`. O que persiste é o texto extraído, editável |
| PDF | Fora. Se o arquivo for PDF, a tela recusa e pede colar o texto ou enviar `.txt`, `.md` ou `.docx` |
| Variável do prompt | `{{job_description}}`. Obrigatória no template para disparar a avaliação |
| Versão | Cada gravação bem-sucedida gera versão nova. A avaliação guarda a versão usada |
| Vazio | Texto vazio depois de trim **não** grava e **não** dispara IA. A triagem determinística **roda** sem job description |
| Quem recebe | Só o payload de quem a etapa 2 já podia chamar (elegível com resposta utilizável e incluído no lote). Inelegível não recebe este texto |
| Trajetória | Este texto **não** é `PerfilVagaTrajetoria`. O botão de trajetória continua desabilitado |
| Duplicar projeto | Além dos critérios duros, copia o texto vigente da job description para uma versão nova no projeto novo. Não copia lote, decisões, prompt nem avaliações |

Opção rejeitada: tratar a job description como mais um critério qualitativo cadastrado na lista da etapa 2. A operação pediu variável do prompt e etapa própria, não um item de lista.

---

## 2. Lugar na navegação

Ordem alvo desta revisão (os números da barra mudam; a triagem continua sem LLM):

| Passo | Tela |
|---|---|
| 1 | Projetos |
| 2 | Critérios duros |
| 3 | **Job description** (esta spec) |
| 4 | Importar |
| 5 | Triagem |
| 6 | Prompt |
| 7 | Avaliação por IA |
| — | Resultado |

A tela de critérios qualitativos sai do caminho. Quem a substitui é `specs/revisao/02-analise-por-pergunta.md`.

Sem projeto corrente, esta tela não opera.

---

## 3. Tela

### 3.1 Conteúdo fixo, visível, não editável

No topo:

> Esta descrição é o contexto geral da vaga. A IA recebe este texto na variável do prompt e usa isso para ler as respostas. Cargo, idade e escolaridade continuam na triagem e não são rejulgados aqui.

### 3.2 Entrada

- Editor de texto (o artefato).
- Enviar arquivo: `.txt`, `.md`, `.docx`.
- Encoding de `.txt` e `.md`: o operador escolhe `utf-8` (padrão desta tela) ou `latin-1`. Falha de UTF-8 recusa o arquivo e pede `latin-1` ou colar.
- `.docx`: extrair o texto dos parágrafos, na ordem. Sem texto extraído, recusar. Não há escolha de encoding.
- Extensão diferente, inclusive `.pdf`: recusar, com a frase da secção 1.
- Depois do envio, o texto aparece no editor. Ainda **não** está vigente até **Salvar job description**.

### 3.3 Salvar

- Trim no fim. Texto vazio: não grava, mensagem “A job description está vazia.”
- Gravação válida: nova versão (`jobDescriptionId`, `versao` inteira monotônica por projeto a partir de 1, `texto`, `criadoEm`). A vigente aponta para essa versão.
- Não sobrescreve o texto de uma versão já usada numa avaliação.
- Aviso não bloqueante se o prompt vigente foi salvo com outra versão desta job description: a avaliação por IA fica bloqueada até o operador salvar o prompt de novo (secção 5). A triagem não bloqueia.

---

## 4. Persistência

Por projeto. SQLite, mesmo arquivo da ADR 003.

| Campo | Obrigatório | Notas |
|---|---|---|
| `jobDescriptionId` | sim | ex.: `jd_03` |
| `versao` | sim | inteiro monotônico por projeto |
| `projetoId` | sim | |
| `texto` | sim | o que será interpolado. Sem HTML obrigatório. Quebras de linha do editor permanecem |
| `criadoEm` | sim | |

`Projeto` ganha `jobDescriptionVigenteId` (nulo até a primeira gravação).

Não vai para o LLM: nome de arquivo, caminho local, binário do upload. Só o texto da versão.

---

## 5. Variável no prompt

Na montagem do prompt de um candidato chamado:

1. O prefixo técnico visível na pré-visualização inclui, em frase fixa, que `job_description` é a descrição geral da vaga, contexto de leitura, e que não reabre cargo, idade nem escolaridade.
2. O template vigente contém `{{job_description}}`.
3. A interpolação troca esse delimitador pelo `texto` da versão de job description **embutida na versão do prompt** (snapshot), não por um texto editado na hora e ainda não salvo.

`PromptDoProjeto` desta revisão, no que esta spec acrescenta (o resto do template está na spec 02):

| Campo | Obrigatório para disparar |
|---|---|
| `jobDescriptionVersaoId` | sim, a vigente no momento do save do prompt |
| `jobDescriptionSnapshot` | sim, cópia do `texto` dessa versão |

Se a vigente da job description for outra, o disparo recusa com:

> A job description mudou desde a última versão salva do prompt. Salve o prompt para gerar uma versão com a descrição atual antes de avaliar.

Pré-visualizar pode mostrar a job description vigente mesmo nessa divergência. Pré-visualizar não chama o LLM.

Placeholder proibido continua proibido: `{{idade}}`, `{{cargo}}`, `{{escolaridade}}`, nome, cidade, equipe, status legado.

---

## 6. O que esta etapa não faz

- Não elimina candidato.
- Não chama LLM ao abrir, colar, enviar arquivo ou salvar.
- Não entra na comparação de cargo, idade ou escolaridade.
- Não substitui o mapeamento das colunas de resposta.
- Não é enviada para inelegível, nem para elegível sem resposta utilizável, nem para quem foi desmarcado no lote.

---

## 7. Critérios de aceite

### CA-JD-01 — Salvar texto

Given um projeto aberto e o editor com texto não vazio após trim  
When o operador salva  
Then existe versão nova vigente com esse texto  
And nenhuma chamada externa ocorreu

### CA-JD-02 — Vazio não grava

Given o editor só com espaços  
When o operador salva  
Then não há versão nova  
And a mensagem diz que a job description está vazia

### CA-JD-03 — PDF recusado

Given um arquivo `.pdf`  
When o operador envia  
Then a tela recusa  
And o editor vigente não muda

### CA-JD-04 — Triagem sem job description

Given critérios duros válidos, lote importado e nenhuma job description salva  
When o operador executa a triagem  
Then o lote é avaliado como na spec de triagem  
And ninguém é aceito ou recusado por falta de job description

### CA-JD-05 — IA bloqueada sem descrição vigente no prompt

Given elegíveis com resposta e prompt salvo sem `jobDescriptionVersaoId` da descrição vigente  
When o operador dispara a avaliação por IA  
Then não há chamada externa  
And a mensagem pede salvar o prompt com a descrição atual

### CA-JD-06 — Inelegível não recebe o texto

Given um inelegível e uma job description vigente  
When a avaliação por IA é disparada  
Then esse candidato não gera chamada  
And o texto da vaga não sai no payload dele

### CA-JD-07 — Duplicar copia a descrição

Given projeto A com job description vigente  
When o operador duplica A  
Then o projeto novo tem o mesmo texto numa versão própria  
And não copia candidatos nem avaliações

### CA-JD-08 — Versão usada não muda

Given uma avaliação gravada com `jd_01`  
When o operador salva `jd_02`  
Then a avaliação antiga continua apontando para `jd_01`

---

## 8. Fora desta spec

- Rubrica das notas e ranking (`specs/revisao/03-rankings.md`)
- Forma do par pergunta/resposta (`specs/revisao/02-analise-por-pergunta.md`)
- Parser de PDF
- Trajetória profissional
