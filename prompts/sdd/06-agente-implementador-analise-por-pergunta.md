# PROMPT — AGENTE IMPLEMENTADOR DA ANÁLISE POR PERGUNTA

Você implementa só `specs/revisao/02-analise-por-pergunta.md`. A job description já está no código. Este agente troca a base da avaliação por IA: a pergunta passa a ser o cabeçalho da coluna. Não implementa a spec 03.

## 1. Missão

Tirar a etapa de critérios qualitativos do fluxo. No disparo novo, a IA cruza três coisas: o cabeçalho da coluna (a pergunta), o texto da célula (a resposta) e a job description já embutida no prompt.

O gate de quem pode ir ao modelo não muda: só elegível, com resposta utilizável, marcado no lote, com job description e prompt alinhados. Inelegível não gera chamada.

O botão **Avaliar trajetória** continua visível, desabilitado, e não dispara request.

## 2. Fontes, nesta ordem

Leia antes de alterar código:

1. `specs/revisao/02-analise-por-pergunta.md` — o que implementar. Critérios CA-P-01 a CA-P-07.
2. `specs/revisao/01-job-description.md` — já implementada. Não refaça a tela, o versionamento nem o bloqueio de prompt desalinhado com a job description.
3. `specs/history.md` — entrada de 2026-09-23. No disparo novo, esta spec prevalece sobre `specs/sprint-1/avaliacao-ia-chatbot.md` nas partes em conflito. Não reescreva essa spec antiga.
4. `specs/adr/007-privacidade-e-seguranca-local.md`.

Leia o código atual em `apps/api` e `apps/web` e estenda. A job description está em `apps/api/job_description`, `apps/api/routers/job_description.py` e `apps/web/src/pages/JobDescription.tsx`.

`specs/revisao/03-rankings.md` é só contexto do que **não** fazer agora. As notas existem no JSON porque o schema desta spec exige. A média, o zeramento e as posições não.

## 3. Decisões já fechadas

Não escolha de novo.

- Some da navegação o item **Critérios qualitativos** e a rota correspondente. A barra fica: Critérios duros, Job description, Importar, Triagem, Prompt, Avaliação IA, Resultado. Renumere esses passos. Sem projeto, as telas de projeto não operam.
- O disparo novo não lê `CriteriosQualitativos`. Não exige `criteriosQualitativos` nem `{{criterios_qualitativos}}`. Linhas antigas dessa tabela podem ficar no banco. Não é obrigatório apagá-las.
- Some o bloqueio “os critérios qualitativos mudaram desde o prompt”. O bloqueio da job description permanece, com a mensagem que já existe.
- A pergunta é o cabeçalho da coluna, depois de strip, sem resumir e sem inventar texto. Exemplo que o teste deve usar: `Como você identifica as necessidades do cliente e personaliza sua abordagem para o atendimento?`
- A resposta é a célula dessa coluna. `perguntaId` é `p1`, `p2`, `p3`, … na ordem em que as colunas foram confirmadas no mapeamento. A mesma ordem produz o mesmo id em todas as linhas do lote.
- Três colunas mapeadas são três pares. Zero colunas mapeadas: a avaliação por IA não roda.
- Par cujo texto, depois de string, strip e colapso de whitespace, fica vazio não entra no prompt. As outras perguntas da mesma linha entram.
- Cabeçalho vazio depois de strip não pode ser confirmado como coluna de resposta. Mensagem: “A coluna de resposta precisa de um nome, porque esse nome é a pergunta.”
- Na importação, texto fixo: “O nome da coluna é a pergunta. A IA cruza a resposta do candidato com essa pergunta e com a job description. Não há critérios qualitativos separados.”
- Cargo, idade e escolaridade da triagem não entram nessa lista, salvo se o operador mapear de novo a mesma coluna como resposta.
- O payload do candidato chamado leva a job description do snapshot do prompt, os pares utilizáveis e o `candidatoId`. Não leva nome, idade, cargo, escolaridade, cidade, telefone, e-mail, busca LKD, status legado, nem lista de critérios qualitativos.
- Uma HTTP por candidato selecionado. Pré-visualizar não chama o provedor. Retry de rede continua só para rede, timeout e 5xx. JSON inválido não é retry de rede. Uma tentativa de reparo de JSON; depois `falha_avaliacao`, sem perfil inventado, sem nota persistida, com `DecisaoTriagem` intacta.
- Salvar o prompt exige `{{job_description}}`, `{{perguntas_respostas}}` e `{{candidato_id}}`. Sem algum deles, recusar com: “O prompt precisa das variáveis da job description, das perguntas e respostas e do identificador.”
- Salvar com `{{criterios_qualitativos}}` recusa com: “Critérios qualitativos não fazem mais parte da avaliação. A IA cruza cada pergunta (nome da coluna) com a resposta e com a job description.”
- Continuam proibidos `{{idade}}`, `{{cargo}}`, `{{escolaridade}}`, pedido para julgar idade, cargo ou escolaridade, nome, cidade, equipe, status legado e cadeia de raciocínio oculta.
- Cada save de prompt gera versão nova e copia `jobDescriptionVersaoId` e `jobDescriptionSnapshot`, como já faz a spec 01.
- Se o template vigente ainda tiver o formato antigo, o editor mostra essa versão e a ação **Usar o modelo desta revisão**. A ação preenche o editor com o corpo da secção 5.4 da spec e não salva sozinha. O prefixo da secção 5.3 substitui as instruções técnicas de formato, aparece na pré-visualização e não é colado de novo dentro do texto editável.
- A forma injetada de `{{perguntas_respostas}}` é a da secção 5.2, um bloco por par, com `Pergunta p1`, `Cabeçalho:` e `Resposta:`.
- JSON de disparo novo, chaves exatas: `perfil`, `por_pergunta`, `trechos`, `nota_tecnica`, `nota_comportamental`. Regras de `por_pergunta`, `trechos` e notas na secção 6 da spec. Chave extra, lista de tamanho errado, id trocado, trecho que não está na resposta, nota ausente ou fora de 0–100: falha.
- `sem_informacao` exige trecho vazio. `atende`, `atende_parcialmente` e `nao_atende` exigem trecho não vazio contido na resposta daquela pergunta, comparado depois de colapsar whitespace. Na tela, `sem_informacao` aparece como “sem informação para julgar esta pergunta”, nunca como pergunta atendida.
- Disparo novo não calcula nem grava `compativel`, `parcial` ou `incompativel`. A tela de resultado de disparo novo não usa esses rótulos como veredito. Mostra, por pergunta: cabeçalho, resultado, justificativa e trecho; mais perfil, versão do prompt, versão da job description e tokens.
- Avaliação já gravada no schema antigo permanece. Não invente `por_pergunta` nem nota para ela. Reimportar o lote continua apagando as avaliações daquele projeto.
- `nota_tecnica` e `nota_comportamental` são persistidas quando o schema passa, nos inteiros que o modelo mandou. Não calcule `nota_final`. Não zere a nota técnica. Não calcule posição. Não monte ranking nem o Excel da spec 03.

## 4. O que construir

1. Tirar critérios qualitativos do menu e da rota. O disparo não consulta essa lista.
2. Texto e validação de cabeçalho na importação, como na secção 3.
3. Trocar a montagem do prompt: `{{perguntas_respostas}}` no lugar de critérios qualitativos. Manter `{{job_description}}` e `{{candidato_id}}`.
4. Trocar o prefixo técnico e o template inicial pelos textos das secções 5.3 e 5.4. Ação **Usar o modelo desta revisão** no editor de prompt.
5. Validar o JSON novo. Persistir `por_pergunta`, trechos, perfil, as duas notas, versão do prompt e versão da job description. Falha não grava nota nem perfil.
6. Ajustar a tela de resultado para o disparo novo, secção 7.
7. Testes automatizados CA-P-01 a CA-P-07.
8. Testes já existentes da job description e do gate de elegível que salvam template com `{{criterios_qualitativos}}` precisam passar a usar os delimitadores desta revisão. Não afrouxe o gate: inelegível continua sem chamada; elegível sem resposta continua aguardando; job description desalinhada do prompt continua bloqueando.

## 5. Fora desta implementação

- `specs/revisao/03-rankings.md`: sem média, sem pesos, sem desempate, sem posição “2 de 15”, sem filtro de ranking, sem zeramento quando toda pergunta é `sem_informacao`, sem botão de exportar o Excel de notas.
- Refazer upload, versão ou tela da job description.
- Mudar cargo, idade ou escolaridade.
- Trajetória, login, funil do legado, leitor de PDF.
- Reescrever spec, ADR ou contrato. Se um detalhe da spec 02 estiver impossível, pare nesse ponto, descreva o bloqueio e não invente outra regra.

## 6. Pronto quando

- CA-P-01 a CA-P-07 passam, e os CA-JD já existentes continuam passando.
- Um disparo de elegível com três colunas manda os três cabeçalhos, as três respostas e a job description, e não manda critérios qualitativos.
- Célula vazia não entra. Inelegível não gera chamada.
- Template com `{{criterios_qualitativos}}` não salva.
- Trecho que não está na resposta vira `falha_avaliacao`, sem nota persistida e sem alterar a triagem.
- A tela de resultado do disparo novo mostra a pergunta e não mostra compatível, parcial ou incompatível como veredito.
- O navegador não chama o provedor. O botão Avaliar trajetória não chama a API.

Não declare a entrega pronta só com a tela estática. Rode os testes e um fluxo em que a pergunta montada é o cabeçalho da coluna.
