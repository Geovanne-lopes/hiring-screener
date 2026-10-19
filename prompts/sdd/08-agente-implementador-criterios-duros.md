# PROMPT — AGENTE IMPLEMENTADOR DOS CRITÉRIOS DUROS

Você implementa só `specs/revisao/04-criterios-duros-cargo-empresa-idade.md`. A triagem, a job description, a análise por pergunta e os rankings já estão no código. Este agente muda a comparação de cargo, acrescenta cargo bloqueado e empresa bloqueada, e ensina a idade a ler `37 anos e 2 meses`.

## 1. Missão

A triagem determinística passa a aceitar um cargo quando as palavras da frase cadastrada aparecem seguidas dentro da célula. Masculino e feminino se equivalem. As únicas abreviações automáticas são `Sr`, `Pl` e `Jr`. Não há tradução para o inglês.

A escolaridade continua igualdade exata. Nada disto chama LLM. O botão **Avaliar trajetória** continua visível, desabilitado, e não dispara request.

## 2. Fontes, nesta ordem

Leia antes de alterar código:

1. `specs/revisao/04-criterios-duros-cargo-empresa-idade.md` — o que implementar. Critérios CA-CD-01 a CA-CD-08.
2. `specs/history.md` — entrada de 2026-09-23 sobre contains, gênero e abreviações. Onde divergir de `specs/sprint-1/triagem-deterministica.md`, vale a spec 04. Não reescreva a spec da etapa 1.
3. `apps/api/triagem/avaliar.py` — a função `_cargo_bate_com_aceito` é a exceção antiga do traço. Substitua essa regra. Não a conserve por cima do contains.

## 3. Decisões já fechadas

Não escolha de novo.

- Cargo aceito: a frase casa se as palavras dela aparecem seguidas e na mesma ordem dentro do cargo da célula. Não precisa ser o texto inteiro.
- `/`, `|`, `-`, `–`, `—`, vírgula e ponto-e-vírgula viram espaço antes de separar as palavras. `Assistente comercial` casa com `Assistente Comercial - Pleno` e com `Assistente Comercial pleno`.
- Acento e maiúscula continuam ignorados. `Sênior` e `Senior` são o mesmo token.
- Gênero, sem lista e sem IA. Em cada palavra já normalizada: se termina em `o` ou `a` e o miolo tem pelo menos 4 caracteres, troque `o`↔`a` (`executivo`↔`executiva`, `pleno`↔`plena`). Se termina em `or` ou `ora` e o miolo tem pelo menos 4 caracteres, troque `or`↔`ora` (`coordenador`↔`coordenadora`, `vendedor`↔`vendedora`). Não faça `gestor`→`gerente`. Não tire `de` nem `e`. Não traduza.
- Abreviações fixas, nos dois sentidos, só como palavra inteira. Não há tela para incluir outros pares.

| Forma por extenso | Abreviação |
|---|---|
| Sênior / Senior | Sr |
| Pleno / Plena | Pl |
| Júnior / Junior | Jr |

- `Sr.`, `Pl.` e `Jr.` com ponto no fim contam igual, sem o ponto. `Pl` não casa dentro de `exemplo` nem de `complementar`.
- Cadastrar `Sênior` também casa `Senior`, `Sr` e `Sr.`. Cadastrar `Pleno` também casa `Plena`, `Pl` e `Pl.`. Cadastrar `Júnior` também casa `Junior`, `Jr` e `Jr.`. Cadastrar `Sr` também casa `Sênior`.
- `Business Executive` não casa com `Executivo de Negócios`. Inglês só entra se essa frase estiver escrita na lista.
- `Vendedor` casa com `Vendedor Externo`. Quem não quiser o externo coloca `Externo` nos cargos bloqueados.
- Não reduzir o cargo à primeira palavra. O texto original da célula continua gravado. O resultado mostra lido → palavras comparadas.
- Na tela de cargos, ao lado de cada item, mostrar as formas que também entram.
- Lista **Cargos bloqueados** no mesmo bloco dos aceitos. Se o cargo casar com um bloqueado, é inelegível mesmo que também tenha casado com um aceito. Motivo `cargo_bloqueado`, citando o termo como o operador digitou.
- Bloco de cargos ativo com aceitos e bloqueados vazios: recusa o lote inteiro e explica. Não aceita todo mundo em silêncio.
- Só aceitos preenchidos: aplica o contains. Bloqueio não elimina.
- Aceitos e bloqueados preenchidos: precisa casar com um aceito e não casar com nenhum bloqueado.
- Só bloqueados preenchidos: não há filtro positivo. Elimina quem casar com o bloqueio.
- Bloco de cargos inativo: nenhuma das duas listas elimina.
- Célula de cargo vazia, com o bloco ativo: `dado_obrigatorio_ausente_ou_invalido`. Não fica elegível.
- Empresas bloqueadas: bloco novo, depois de Cargos e antes de Idade, com ativo/inativo e lista editável. Sem gênero e sem `Sr`/`Pl`/`Jr`. A mesma partição em palavras, só com acento, maiúscula e pontuação. `Cielo` casa com `Cielo S.A.` e com `Grupo / Cielo`. Não casa no meio de outra palavra.
- Empresa inativa não elimina e não exige coluna. Ativa com lista vazia recusa o lote. Ativa com lista e sem coluna mapeada recusa o lote. Célula que casa: `empresa_bloqueada`. Célula vazia com o bloco ativo: dado inválido no critério empresa. Célula que não casa: este critério não elimina.
- Destino novo de importação `empresa`, opcional para importar. Se existir coluna `Empresa` e o operador ainda não escolheu outra, sugerir. O valor guardado é o texto da célula. Duplicar projeto copia este bloco com os critérios duros.
- Empresa, cargo e idade não vão ao LLM, nem à job description, nem às perguntas, salvo se o operador mapear a mesma coluna de novo como resposta.
- Idade inclusiva nos dois extremos. `37`, `37.0`, `37,0`, `37 Anos`, `37 - Anos`, `37anos`, `37 Años`, `37 años`, `37 years`, `37 anos e 2 meses`, `37 anos + 2 meses` e `37 anos + 11 meses` valem 37. Meses não somam. Unidades de ano, depois da normalização: `ano`, `anos`, `year`, `years`. Unidades de mês ignoradas: `mes`, `meses`, `month`, `months`.
- Sem a palavra de ano, a célula precisa ser um inteiro só. Inválido, sem chutar: vazio, `adulto`, `entre 30 e 37`, `30 a 40 anos`, `37,5`, inteiro fora de 1 a 120. `#NAME?` continua lixo.
- O resultado da idade mostra lido `37 anos e 2 meses` → comparado `37`.
- Escolaridade permanece igualdade da lista. `Bacharelado` não casa com `Bacharelado em Estatística`.
- Ordem dos motivos: cargo aceito, cargo bloqueado, empresa, idade, escolaridade. Avaliar todos os critérios ativos. Não parar no primeiro.
- Critério salvo antigo, sem `bloqueados` ou sem o bloco de empresas: tratar bloqueados como lista vazia e empresas como inativas. Não quebrar a leitura. A comparação nova de cargo vale na próxima execução.
- Textos fixos da tela, como na secção 7 da spec.

## 4. O que construir

1. Trocar a comparação de cargo. Apagar a regra “só casa se o resto começa com traço, barra ou pipe”.
2. Gênero e as três abreviações, nos dois sentidos, palavra inteira.
3. Lista de cargos bloqueados no bloco de cargos, com as formas que também entram visíveis ao lado.
4. Bloco de empresas bloqueadas, coluna `empresa` na importação, persistência no candidato e no snapshot dos critérios.
5. Parser de idade da secção 6 da spec.
6. Testes CA-CD-01 a CA-CD-08.
7. Testes antigos que exigiam igualdade de cargo, ou que `Assistente Comercial pleno` fosse inelegível por não ter traço, passam a esperar o contains. Não afrouxe a escolaridade. Não deixe cargo, empresa ou idade irem no payload do LLM.

## 5. Fora desta implementação

- Tabela editável de inglês, tradução de cargo, abreviação além de Sr, Pl e Jr.
- `gestor`→`gerente`, stop word, cortar na primeira palavra.
- Contains em escolaridade.
- Mudar job description, prompt, análise por pergunta ou ranking.
- Trajetória, login, funil do legado.
- Reescrever spec ou ADR. Se um detalhe da spec 04 estiver impossível, pare nesse ponto, descreva o bloqueio e não invente outra regra.

## 6. Pronto quando

- CA-CD-01 a CA-CD-08 passam, e a triagem segue sem chamada de LLM.
- `Assistente Comercial pleno` é elegível quando o aceito é `Assistente comercial` e o bloqueio está vazio.
- `Executiva de Negócios` é elegível para `Executivo de Negócios`. `Business Executive` não é.
- `Pleno` bloqueia `Assistente Comercial pleno`, `Plena` e `Pl`, e não bloqueia `Complementar`.
- `Sênior` bloqueia `Analista SR` e `Analista Sr.`. `Júnior` bloqueia `Analista Jr`.
- `Cielo S.A.` cai em `empresa_bloqueada` quando a lista tem `Cielo`. O nome do candidato não vai ao LLM.
- `37 anos e 2 meses` compara como 37. `entre 30 e 37 anos` fica inválido.
- `Bacharelado em Estatística` continua fora de uma lista que só tem `Bacharelado`.
- O botão Avaliar trajetória não chama a API.

Não declare a entrega pronta só com a tela estática. Rode os testes e uma triagem em que `Assistente Comercial pleno` passe e `Analista SR` caia por `Sênior`.
