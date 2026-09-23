# Como usar estes prompts

Estes arquivos não implementam o sistema. Eles instruem agentes a escrever especificações, no mesmo método do prompt de Spec-Driven Development do projeto anterior (um agente analisa o que existe, registra decisões e produz contratos; outro agente, depois, implementa só o que estiver especificado).

Não copie o domínio daquele prompt (aplicativo Android, ideias, estratégias, papéis de operador/gestor/líder, MongoDB, Gemini obrigatório). O que se reaproveita é o método: fontes de verdade, precedência, ADR, critérios Given/When/Then, rastreabilidade e Definition of Done.

## Ordem

Abra um agente novo para cada arquivo. Não junte os quatro no mesmo chat.

1. `00-agente-orquestrador.md`
   Só rode os próximos quando existirem `specs/00-visao-produto.md`, `specs/01-legado-e-gaps.md`, `specs/02-arquitetura.md`, `specs/03-contratos-compartilhados.md`, `specs/history.md` e as ADRs indicadas nesse prompt.
2. `01-agente-triagem-deterministica.md`
3. `02-agente-avaliacao-ia-chatbot.md`
   Este agente precisa da spec de triagem, porque a IA só roda depois do filtro determinístico.
4. `03-agente-trajetoria-profissional.md`
   Este agente especifica a sprint posterior. Ele não puxa essa função para a primeira entrega.

Nenhum desses agentes escreve código de produto, testa modelo, chama API de LLM ou gera a tela.

## O que cada um entrega

| Agente | Etapa | Pode criar |
|---|---|---|
| Orquestrador | Recorte do produto, legado, arquitetura, contratos entre etapas | `specs/00` a `specs/03`, `specs/adr/`, `specs/history.md`, `specs/glossario.md` |
| Triagem | Critérios duros de aceite e recusa, sem IA | `specs/sprint-1/triagem-deterministica.md` |
| Avaliação por IA | Respostas do chatbot, perfil e compatibilidade com a vaga | `specs/sprint-1/avaliacao-ia-chatbot.md` |
| Trajetória | Botão futuro a partir de cargos, resumos e headlines | `specs/sprint-2/trajetoria-profissional.md` |

Se um agente precisar mudar contrato de outro, ele não reescreve o arquivo do outro. Ele acrescenta uma entrada em `specs/history.md` com o conflito, o impacto e a mudança proposta.
