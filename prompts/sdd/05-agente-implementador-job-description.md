# PROMPT — AGENTE IMPLEMENTADOR DA JOB DESCRIPTION

Você implementa só `specs/revisao/01-job-description.md`. A sprint 1 já está no código. Este agente acrescenta a etapa da job description. Não implementa as specs 02 e 03.

## 1. Missão

Encaixar a descrição geral da vaga como etapa própria, depois dos critérios duros e antes da importação. O texto salvo vira a variável `{{job_description}}` do prompt da avaliação por IA.

A triagem determinística continua sem LLM e sem depender deste texto. O botão **Avaliar trajetória** continua visível, desabilitado, e não dispara request.

## 2. Fontes, nesta ordem

Leia antes de alterar código:

1. `specs/revisao/01-job-description.md` — o que implementar. Critérios CA-JD-01 a CA-JD-08.
2. `specs/history.md` — entrada de 2026-09-23. Onde a revisão divergir da etapa 2, vale a spec 01 **somente** no que este prompt manda construir.
3. `specs/sprint-1/avaliacao-ia-chatbot.md` — prompt, gate e avaliação que já existem. Não reescreva esse arquivo.
4. `specs/adr/003-persistencia-sqlite.md`, `specs/adr/004-provedor-llm-configuravel.md`, `specs/adr/007-privacidade-e-seguranca-local.md`.

Leia o código atual em `apps/api` e `apps/web` e estenda. Não recrie a sprint 1.

`specs/revisao/02-analise-por-pergunta.md` e `specs/revisao/03-rankings.md` são só contexto do que **não** fazer agora.

## 3. Decisões já fechadas

Não escolha de novo.

- Web local, sem login. React em `apps/web`. FastAPI em `apps/api`. SQLite no mesmo `SCREENER_DB_PATH`.
- A job description é texto da vaga, versionado por projeto. Não é critério duro e não elimina ninguém.
- Entrada: colar no editor ou enviar `.txt`, `.md` ou `.docx`. Persiste o texto extraído. O envio só preenche o editor. Vigente só depois de **Salvar job description**.
- `.txt` e `.md`: encoding escolhível, padrão `utf-8`, também `latin-1`. UTF-8 inválido recusa e pede latin-1 ou colar.
- `.docx`: texto dos parágrafos, na ordem. Sem texto, recusa. Sem seletor de encoding. Pode acrescentar dependência só para isso.
- `.pdf` e qualquer outra extensão: recusar. Sem leitor de PDF. Mensagem pede colar o texto ou enviar `.txt`, `.md` ou `.docx`.
- Texto vazio depois de trim não grava. Mensagem: “A job description está vazia.”
- Cada save válido cria versão nova (`jobDescriptionId`, `versao` monotônica por projeto a partir de 1, `texto`, `criadoEm`). Não atualiza linha de versão já gravada.
- `Projeto` aponta a vigente em `jobDescriptionVigenteId`.
- Duplicar projeto copia os critérios duros **e** o texto vigente da job description, como versão nova no projeto novo. Não copia lote, decisões, prompt nem avaliações.
- No prompt, o delimitador é `{{job_description}}`. A interpolação usa o snapshot embutido na versão do prompt, não o rascunho do editor.
- Salvar o prompt grava `jobDescriptionVersaoId` e `jobDescriptionSnapshot` da job description vigente naquele momento.
- Sem job description vigente, a avaliação por IA não dispara. A triagem dispara.
- Se a job description vigente for outra que a embutida no prompt vigente, a avaliação por IA recusa com: “A job description mudou desde a última versão salva do prompt. Salve o prompt para gerar uma versão com a descrição atual antes de avaliar.” A triagem não bloqueia. A tela de job description mostra esse aviso, sem impedir o save da descrição.
- Pré-visualizar o prompt pode mostrar a job description vigente mesmo nessa divergência. Pré-visualizar não chama o LLM.
- O prefixo técnico visível na pré-visualização ganha a frase fixa: o texto de job description é a descrição geral da vaga, contexto de leitura, e não reabre cargo, idade nem escolaridade.
- Inelegível não gera chamada e o texto da vaga não entra no payload dele. O mesmo vale para elegível sem resposta utilizável e para quem foi desmarcado no lote. Nome, idade, cargo, escolaridade, cidade e status legado continuam fora do payload.
- A avaliação gravada continua apontando para a versão de job description daquele disparo. Salvar outra versão não reescreve a avaliação antiga.
- Abrir, colar, enviar arquivo ou salvar não chama o LLM.

## 4. O que construir

1. Tela **Job description** no projeto corrente, item de menu **3. Job description**, entre Critérios duros e Importar. Os passos seguintes da barra sobem um número. Sem projeto, a tela não opera.
2. Texto fixo no topo, como na secção 3.1 da spec.
3. Editor, envio de arquivo, save com as regras da secção 3.
4. Tabela de versões no SQLite. `create_all` não altera tabela que já existe: se precisar de coluna nova em `projetos` ou `prompts` ou `avaliacoes_ia`, faça o ajuste na abertura do banco, no mesmo espírito de `persistencia/db.py`.
5. `duplicar` copia a job description vigente.
6. Montagem do prompt: exige o delimitador para disparar a avaliação. Interpola o snapshot. Guarda na avaliação a versão usada.
7. Bloqueio de disparo da secção 5 da spec, com a mensagem única.
8. Testes automatizados CA-JD-01 a CA-JD-08.

A tela de critérios qualitativos, `{{criterios_qualitativos}}`, a compatibilidade calculada e o JSON atual da avaliação **permanecem**. Esta entrega não os remove. O template vigente que já existe precisa passar a aceitar `{{job_description}}` junto com os delimitadores que já tem. Não troque o template pelo da spec 02.

## 5. Fora desta implementação

- `specs/revisao/02-analise-por-pergunta.md`: não apague a tela de critérios qualitativos, não troque `por_criterio` por `por_pergunta`, não recuse `{{criterios_qualitativos}}`.
- `specs/revisao/03-rankings.md`: sem nota técnica, nota comportamental, ranking nem Excel novo de resultado.
- Trajetória, login, funil do legado, treino de modelo, leitor de PDF.
- Reescrever spec, ADR ou contrato para caber num atalho. Se um detalhe da spec 01 estiver impossível, pare nesse ponto, descreva o bloqueio e não invente outra regra.

## 6. Pronto quando

- CA-JD-01 a CA-JD-08 passam.
- Dá para abrir um projeto, salvar uma job description, ver que a triagem ainda roda sem ela, e ver que a avaliação por IA não dispara enquanto o prompt não estiver salvo com a versão vigente.
- Um arquivo `.pdf` é recusado e o texto vigente não muda.
- Duplicar o projeto leva o texto da descrição e não leva o lote.
- O navegador não chama o provedor de LLM. Inelegível não leva a job description no payload.
- O botão Avaliar trajetória não chama a API.

Não declare a entrega pronta só com a tela estática. Rode os testes e o fluxo de salvar a descrição de verdade.
