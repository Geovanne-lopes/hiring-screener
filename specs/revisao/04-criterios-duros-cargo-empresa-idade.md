# Revisão — Cargos, empresas bloqueadas e idade com “anos”

Spec da triagem determinística. Muda a comparação de **cargo**, acrescenta **cargo bloqueado** e **empresa bloqueada**, e ensina a idade a ler `37 Anos`. Não chama LLM. Não mexe em escolaridade, job description, análise por pergunta nem ranking.

Não reescreve `specs/sprint-1/triagem-deterministica.md`. Onde divergir, vale este arquivo (`specs/history.md`).

O código de hoje já não é igualdade pura: `Assistente comercial` aceita `Assistente Comercial - Pleno` porque o resto começa com traço, e recusa `Assistente Comercial pleno`. Esta spec substitui essa exceção.

---

## 1. Decisões fechadas

| Tema | Decisão |
|---|---|
| Cargo aceito | A frase aceita entra se aparecer como palavras seguidas dentro do cargo da célula. Não precisa ser o texto inteiro |
| Traço, barra, pipe | Viram espaço antes de comparar. `Assistente Comercial - Pleno` e `Assistente Comercial pleno` batem com `Assistente comercial` |
| Acento e maiúscula | Continuam de fora, como já estão. `Sênior` e `Senior` são o mesmo token |
| Gênero | Sem IA. Regra mecânica, visível: `executivo`/`executiva`, `coordenador`/`coordenadora`, `pleno`/`plena` |
| Abreviação | Só três, fixas, nos dois sentidos: `Sênior`↔`Sr`, `Pleno`↔`Pl`, `Júnior`↔`Jr`. Sem tabela editável |
| Inglês | Não traduz. `Business Executive` só entra se o operador escrever essa frase na lista |
| Cargo bloqueado | Se o cargo contiver um termo da lista de bloqueio, é inelegível, mesmo que também tenha batido com um cargo aceito |
| Empresa bloqueada | Critério duro novo. Se a empresa mapeada contiver um nome da lista, é inelegível |
| Idade | `37`, `37 Anos`, `37 - Anos`, `37 Años` e `37 anos e 2 meses` viram 37. Os meses não entram na conta. A faixa inclusiva não muda |
| Escolaridade | Igualdade da lista, como na spec da etapa 1. Sem contains |
| Primeira palavra | Continua proibido cortar o cargo na primeira palavra |
| LLM | Cargo, empresa e idade não entram no prompt |

Opção rejeitada: mandar cargo, gênero ou empresa ao modelo para “resolver sinônimo”. A triagem segue sem token.

---

## 2. Sem IA: o que a regra cobre

Três camadas, todas locais. A tela mostra, ao lado de cada item, as formas que também entram.

### 2.1 Já existia

Trim, espaços, acento e maiúscula. `Executivo de Negócios` comparado é `executivo de negocios`.

### 2.2 Gênero, mecânico

Sobre cada palavra já normalizada, dois pares só:

- a palavra termina em `o` ou `a`, o miolo antes dessa letra tem pelo menos 4 caracteres, e a outra forma troca `o`↔`a` (`executivo`↔`executiva`, `pleno`↔`plena`);
- a palavra termina em `or` ou `ora`, o miolo antes disso tem pelo menos 4 caracteres (`coordenador`↔`coordenadora`).

Não aplica `gestor`→`gerente`, não tira `de`/`e`, não traduz.

### 2.3 Abreviações fixas

Três pares, nos dois sentidos, só como palavra inteira. Não há tela para incluir outros. Não é tradução.

| Forma por extenso | Abreviação |
|---|---|
| Sênior / Senior | Sr |
| Pleno / Plena | Pl |
| Júnior / Junior | Jr |

`Sênior` e `Senior` já coincidem pelo acento. `Plena` também entra pelo gênero. `Sr.`, `Pl.` e `Jr.` com ponto no fim contam igual à abreviação sem ponto.

`PL` não casa dentro de `exemplo` nem de `complementar`. Vale para cargo aceito e cargo bloqueado. Não vale para empresa nem para escolaridade.

`Business Executive` não entra por causa de `Executivo`. Inglês só casa se a frase estiver escrita na lista.

---

## 3. Como o cargo é comparado

Isto substitui a igualdade e a exceção do traço.

1. Normalizar (secção 2.1).
2. Trocar `/`, `|`, `-`, `–`, `—`, vírgula e ponto-e-vírgula por espaço. Colapsar espaços. Separar em palavras.
3. Uma frase casa quando as palavras dela aparecem **seguidas e na mesma ordem** dentro das palavras da célula. Cada palavra pode usar o par de gênero da secção 2.2 e, se for uma das três, a abreviação da secção 2.3.

`Assistente comercial` casa com `Assistente Comercial pleno` e com `Assistente Comercial - Pleno`.

`Executivo de Negócios` casa com `Executiva de Negócios`. Não casa com `Business Executive`.

`Vendedor` passa a casar com `Vendedor Externo`, porque `vendedor` é uma palavra lá dentro. Quem não quiser o externo coloca `Externo` na lista de bloqueio, ou cadastra uma frase mais longa. Isso é o contains pedido. A exceção antiga (“só se houver traço”) deixa de existir.

Cadastrar `Sênior` também casa `Senior`, `Sr` e `Sr.`. Cadastrar `Pleno` também casa `Plena`, `Pl` e `Pl.`. Cadastrar `Júnior` também casa `Junior`, `Jr` e `Jr.`. O contrário também: cadastrar `Sr` casa `Sênior`.

O cargo original continua gravado. O resultado mostra lido → palavras comparadas.

Não reduzir à primeira palavra.

---

## 4. Lista de cargos bloqueados

No mesmo bloco **Cargos aceitos**, segunda lista: **Cargos bloqueados**. Incluir, remover, forma digitada e formas que também entram.

| Situação do bloco ativo | Efeito |
|---|---|
| Aceitos e bloqueados vazios | A execução do lote inteiro bloqueia, com erro. Não aceita todo mundo em silêncio |
| Só aceitos preenchidos | Igual a hoje, com a comparação nova. Bloqueio não elimina ninguém |
| Aceitos e bloqueados preenchidos | Precisa casar com um aceito **e** não casar com nenhum bloqueado. O bloqueio ganha |
| Só bloqueados preenchidos | Não há filtro positivo. Elimina quem casar com o bloqueio. Os outros passam neste critério |

Bloco de cargos **inativo**: nenhuma das duas listas elimina.

Exemplos com aceito `Assistente comercial` e bloqueados `Sênior` e `Pleno`:

| Célula | Resultado |
|---|---|
| Assistente comercial | Elegível neste critério |
| Assistente Comercial pleno | Inelegível. Motivo: cargo bloqueado `Pleno` (também casa `Plena` e `Pl`) |
| Assistente Comercial - Sênior | Inelegível por `Sênior` (também casa `Senior` e `Sr`) |
| Analista SR | Inelegível por `Sênior`, porque `Sr` é a abreviação fixa |
| Analista Jr | Inelegível se `Júnior` estiver no bloqueio. `Jr` é a abreviação fixa |

Motivo novo: `cargo_bloqueado`. A mensagem cita o cargo lido, a forma comparada e o termo bloqueado como o operador digitou.

Vazio na célula de cargo, com o bloco ativo, continua `dado_obrigatorio_ausente_ou_invalido`. Não fica elegível.

---

## 5. Empresas bloqueadas

Bloco novo, depois de Cargos e antes de Idade. Interruptor ativo/inativo. Lista editável de nomes. Não usa gênero nem as abreviações `Sr` / `Pl` / `Jr`.

Comparação: a mesma partição em palavras da secção 3, só com acento, maiúscula e pontuação. `Cielo` casa com `Cielo S.A.` e com `Grupo / Cielo`. Não casa com um nome que apenas contenha essas letras no meio de outra palavra.

| Estado | Efeito |
|---|---|
| Inativo | Não elimina. Não exige coluna |
| Ativo e lista vazia | Bloqueia a execução do lote. Não aceita todo mundo em silêncio |
| Ativo, lista preenchida, coluna não mapeada | Bloqueia a execução |
| Ativo e a célula casa com um nome da lista | Inelegível. Motivo `empresa_bloqueada` |
| Ativo e a célula, depois de tirar espaço, está vazia | Inelegível. Motivo `dado_obrigatorio_ausente_ou_invalido` no critério empresa |
| Ativo e a célula não casa | Este critério não elimina |

Importação: destino novo `empresa`, opcional para importar. Se existir coluna `Empresa` (depois de strip do nome) e o operador ainda não escolheu outra, ela vem sugerida. Confirmar mapeamento continua obrigatório. O valor guardado é o texto da célula, sem reescrever.

Empresa não vai ao LLM, não entra na job description e não é pergunta de chatbot, salvo se o operador mapear a mesma coluna de novo como resposta.

Duplicar projeto copia este bloco junto com os outros critérios duros.

---

## 6. Idade com “anos”

A faixa inclusiva permanece: `minima ≤ idade ≤ maxima`.

A célula pode ser um inteiro puro, como hoje (`37`, `37.0`, `37,0`). Também pode ser um inteiro seguido da unidade, com ou sem espaço e com ou sem traço:

- `37 Anos`
- `37 - Anos`
- `37anos`
- `37 Años`
- `37 años`
- `37 years`

A idade comparada é o inteiro que acompanha a unidade de ano, quando ela existe. Unidades de ano, depois da normalização: `ano`, `anos`, `year`, `years`. `Años` já virou `anos`.

Meses não somam na idade. São ignorados o número e a unidade `mes`, `meses`, `month`, `months`, com ou sem `e`, `+` ou traço no meio. `37 anos e 2 meses`, `37 anos + 2 meses` e `37 anos + 11 meses` valem 37. O resultado mostra lido `37 anos e 2 meses` → comparado `37`.

Sem a palavra de ano, a célula precisa ser um inteiro só (`37`, `37.0`, `37,0`).

Inválido, motivo de dado ausente ou inválido, sem chutar:

- célula vazia;
- nenhum inteiro (`adulto`);
- dois números de ano, ou dois inteiros sem deixar claro qual é o ano (`entre 30 e 37`, `30 a 40 anos`);
- parte decimal diferente de zero (`37,5`);
- inteiro fora de 1 a 120.

`#NAME?` continua lixo de fórmula.

---

## 7. Tela

No bloco de cargos, a frase fixa passa a ser:

> A comparação ignora maiúsculas, acentos e espaços extras. Uma frase aceita entra se as palavras dela aparecerem seguidas no cargo. Masculino e feminino se equivalem. As únicas abreviações automáticas são Sr, Pl e Jr. O cargo não é reduzido à primeira palavra e não é traduzido para o inglês.

Texto fixo na lista de bloqueio:

> Se o cargo contiver um destes termos, a pessoa fica inelegível, mesmo que o cargo também esteja na lista de aceitos.

No bloco de empresas:

> Se a empresa contiver um destes nomes, a pessoa fica inelegível. Maiúsculas, acentos e o sufixo S.A. não impedem o encontro.

Na idade, manter a frase dos limites inclusivos e acrescentar:

> `37 Anos`, `37 - Anos`, `37 Años` e `37 anos e 2 meses` contam como 37. Os meses não entram na conta.

Escolaridade conserva o texto e a igualdade atuais.

Salvar critérios continua gerando versão nova. A execução aponta para a versão salva.

---

## 8. Ordem dos motivos

Cargo aceito, cargo bloqueado, empresa, idade, escolaridade. Critério ativo é sempre avaliado. Não para no primeiro motivo.

---

## 9. Critérios de aceite

### CA-CD-01 — Contains com e sem traço

Given aceito `Assistente comercial` e bloqueio vazio  
When o cargo é `Assistente Comercial - Pleno`  
Then é elegível neste critério  
When o cargo é `Assistente Comercial pleno`  
Then também é elegível neste critério

### CA-CD-02 — Gênero sem chamada de modelo

Given aceito `Executivo de Negócios`  
When o cargo é `Executiva de Negócios`  
Then é elegível neste critério  
When o cargo é `Business Executive`  
Then não é elegível neste critério  
And nenhuma chamada externa ocorreu

### CA-CD-03 — Bloqueio ganha do aceito

Given aceito `Assistente comercial` e bloqueado `Pleno`  
When o cargo é `Assistente Comercial pleno`  
Then é inelegível com `cargo_bloqueado`  
And `Plena` e `Pl` também bloqueiam  
And `Pl` não casa dentro de `Complementar`

### CA-CD-04 — Sr, Pl e Jr

Given bloqueado `Sênior`  
When o cargo é `Analista Senior`, ou `Analista SR`, ou `Analista Sr.`  
Then é inelegível  
Given bloqueado `Júnior`  
When o cargo é `Analista Jr`  
Then é inelegível  
Given aceito `Executivo de Negócios` e nenhum bloqueio  
When o cargo é `Business Executive`  
Then não é elegível neste critério

### CA-CD-05 — Lista vazia não aceita em silêncio

Given o bloco de cargos ativo, aceitos vazios e bloqueados vazios  
When a triagem é executada  
Then o lote inteiro é recusado e o erro é explicado

### CA-CD-06 — Empresa

Given `Cielo` na lista de empresas bloqueadas, coluna mapeada  
When a célula é `Cielo S.A.`  
Then é inelegível com `empresa_bloqueada`  
And o nome não vai no payload do LLM

### CA-CD-07 — Idade com unidade

Given faixa 30 a 40, limites inclusivos  
When a célula é `37 Anos`, ou `37 - Anos`, ou `37 Años`, ou `37 anos e 2 meses`, ou `37 anos + 11 meses`  
Then o valor comparado é 37 e a pessoa passa neste critério  
When a célula é `entre 30 e 37 anos`  
Then o motivo é dado inválido e a idade não é chutada

### CA-CD-08 — Escolaridade intacta

Given escolaridade aceita `Bacharelado`  
When a célula é `Bacharelado em Estatística`  
Then continua fora da lista  
And a comparação de escolaridade não usa contains

---

## 10. Fora desta spec

- Traduzir cargo para o inglês, ou ampliar abreviações além de Sr, Pl e Jr
- Copiar `gestor`→`gerente`, stop word ou primeira palavra do legado
- Contains em escolaridade
- Enviar cargo, empresa ou idade ao LLM
- Trajetória profissional
