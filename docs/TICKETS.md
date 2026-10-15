<!-- Caminho relativo: docs/TICKETS.md -->

# Tickets

Uma linha por ticket: identificador, link para o detalhe e uma frase. O detalhe mora no
destino do link (skill `micro-ticket-planner`).

## Em aberto

A ordem da lista é a ordem de execução. Três critérios, nesta precedência: **risco já
publicado** primeiro, depois **o que destrava outros**, depois o resto por tema. Bloqueio é
texto na própria linha, com a dependência nomeada — linha sem dependência nomeada não é
bloqueio, é trabalho que ninguém começou.

Os MT-22 a MT-40 saíram da análise comparativa de harness, em quatro rodadas. O caminho
crítico é MT-22 → MT-23 → MT-25 → MT-26: instrumentar antes de mudar comportamento, porque
mudança sem linha de base não é refutável. Os MT-43 e MT-44 saíram da análise de biblioteca de
terceiros, e são as duas pernas do orçamento de catálogo: medir o teto de cada harness, e
derivar o que é instalado. Os MT-45 a MT-47 são a triagem dessa mesma análise já decidida item
a item: o que foi importado, o que virou seção de skill existente e o que foi recusado.
O MT-49 saiu da leitura de um artigo sobre prompts de raciocínio, e espera o primeiro
experimento controlado, cujo método é o MT-50.

Sem ticket ainda, e sabido: a medição da lista `deny` contra indireção e o experimento de
sandbox do §8 de `docs/interop/isolamento-de-execucao.md` estão dentro do MT-42; não sobra item
sabido fora de ticket.

- [!] [MT-24](tickets/MT-24.md) — Hook de git em camadas: a camada de texto foi medida e fechou 11 vetores; **4 lacunas declaradas** só a camada 1 fecha · furo publicado
- [!] [MT-40](tickets/MT-40.md) — Guarda de vazamento cega a nome de ref e a caminho sob o clone · furo publicado, já vazou uma vez
- [!] [MT-39](tickets/MT-39.md) — Resolver a procedência do acervo importado, e decidir o que fica — bloqueado por autorização do autor do acervo: a redistribuição é desconhecida, e é o item que destrava os outros
- [ ] [MT-41](tickets/MT-41.md) — Verificador do painel não examina seção que ele não conhece
- [ ] [MT-48](tickets/MT-48.md) — Verificador de links varre o que o `.gitignore` ignora, e a conta local deixa de bater com a do CI
- [ ] [MT-42](tickets/MT-42.md) — Medir a fronteira de isolamento, e dar mecanismo ao que o perfil já exige
- [ ] [MT-44](tickets/MT-44.md) — Medir o que cada harness faz com catálogo acima do teto: avisa, corta em silêncio ou não tem limite
- [ ] [MT-43](tickets/MT-43.md) — Derivar na instalação quais skills do acervo entram no projeto — o acervo é 1,66× o único teto observado
- [ ] [MT-45](tickets/MT-45.md) — Abrir a categoria `escrita` e importar o trio de escrita autoral — `invocacao: humano`, não disputa o orçamento de catálogo
- [ ] [MT-46](tickets/MT-46.md) — Skill de reexplicação: a mesma resposta por outro caminho, não a mesma mais longa
- [ ] [MT-47](tickets/MT-47.md) — Dados de teste parciais sem mentir ao compilador, em `teste-primeiro`
- [ ] [MT-49](tickets/MT-49.md) — Afirmação verificável: rodar o EXP-0001 pré-registrado, e só então criar a skill, arquivar inconclusivo ou recusar
- [ ] [MT-22](tickets/MT-22.md) — Colhedor retroativo de métricas de sessão (linha de base do passado)
- [ ] [MT-23](tickets/MT-23.md) — Relatório de métricas com comparação antes/depois
- [ ] [MT-25](tickets/MT-25.md) — Executor de gates: a skill de conclusão tem 217 linhas e nenhum script
- [ ] [MT-26](tickets/MT-26.md) — Lint do próprio `EXPECT`, com corpus de validação
- [ ] [MT-27](tickets/MT-27.md) — Enumerar skills sem `node_modules`, com teste
- [ ] [MT-28](tickets/MT-28.md) — Diagnóstico detecta placeholder não substituído
- [ ] [MT-29](tickets/MT-29.md) — Fronteira negativa nas descrições de skill, com lint — bloqueado por MT-44: custa ~58 B por skill e o teto de cada harness não está medido
- [ ] [MT-31](tickets/MT-31.md) — Mover o catálogo de skills do arquivo de regra para o índice
- [ ] [MT-32](tickets/MT-32.md) — Relocar segurança e fluxo: detalhe para a skill, fluxo para tabela
- [ ] [MT-33](tickets/MT-33.md) — Cliente único para delegação a modelo externo
- [ ] [MT-34](tickets/MT-34.md) — Sonda de capacidade de modelo e protocolo de escolha
- [ ] [MT-35](tickets/MT-35.md) — Roteamento validado das skills de delegação
- [ ] [MT-37](tickets/MT-37.md) — Resolver a sobreposição entre as duas skills de fan-out
- [ ] [MT-36](tickets/MT-36.md) — ADR do hook que recusa — bloqueado por ADR 0009: ela está `Proposed` e diz "hooks como sensor", o hook novo recusa
- [ ] [MT-30](tickets/MT-30.md) — Pin de procedência para fonte externa de skills — a parte de política foi decidida pela [ADR 0021](adr/0021-procedencia-do-acervo.md); resta o mecanismo de pin
- [ ] [MT-14](../docs/adr/0015-biblioteca-privada-em-repositorio-publico.md) — Decidir a ADR 0015: biblioteca privada em repositório público
- [ ] [MT-38](tickets/MT-38.md) — Replay forçado: saliência ou suficiência na escolha de subagente
- [ ] [MT-21](tickets/MT-21.md) — Papéis nomeados: verificar **invocação**, não instalação (falha hoje, de propósito)
- [ ] [MT-7](tickets/MT-7.md) — Medir a nossa verificação contra o laço com score, em gabarito comum
- [ ] [MT-15](tickets/MT-15.md) — Provas adversariais executáveis nas skills de segurança e serviço
- [ ] [MT-16](tickets/MT-16.md) — Ledger de evidência com impressão digital e validade
- [ ] [MT-17](tickets/MT-17.md) — Skill `exercitar-skill`: derivar as racionalizações de observação
- [ ] [MT-18](tickets/MT-18.md) — Skill de disciplina de aprendizado de máquina (anti-vazamento)
- [ ] [MT-2](tickets/MT-2.md) — Skill de núcleo de cálculo C++/CMake: 5 repositórios, nenhum coberto
- [ ] [MT-3](tickets/MT-3.md) — Skill de biblioteca/CLI em Rust: 8 repositórios com `Cargo.toml`
- [ ] [MT-20](tickets/MT-20.md) — Decisão tipada como camada de roteamento — bloqueado por medição no `agentry`: sem ela os pesos são chute
- [ ] [MT-12](tickets/MT-12.md) — UI React — bloqueado por decisão da empresa: só se fecharem React em vez de Svelte
- [ ] [MT-6](tickets/MT-6.md) — Propagar às instalações de `~/dev` — bloqueado por decisão do autor: cada repositório é atualizado quando a própria árvore estiver limpa

## Concluídos

- [x] [MT-50](tickets/MT-50.md) — Experimento controlado de instrução: método, executor com autoteste no CI e worktree de experimentos
- [x] [MT-0](../skills/pr-review-guard/scripts/checar-mensagem-commit.sh) — Painel de tickets e proibição de entrada extra em commit e documentação
- [x] MT-5 — [Regra transversal de comportamento questionador](../skills/perguntar-antes-de-construir/SKILL.md)
- [x] [MT-19](tickets/MT-19.md) — Craft de interface em quatro operações, com playbooks e piso separados
- [x] [MT-13](tickets/MT-13.md) — Verificador de links de Markdown, com máscara de código em linha e âncora do GitHub
- [x] [MT-10](../skills/entrega/pipeline-como-gate/SKILL.md) — CI como gate, com verificador de coerência com o `AGENTS.md`
- [x] [MT-11](../skills/entrega/deploy-reproduzivel/SKILL.md) — Deploy reproduzível: rollback escrito antes, verificação por sinal externo
- [x] MT-8 — [Serviço HTTP em FastAPI, com gate de detecção](../skills/stack/criar-servico-fastapi/SKILL.md) · front: SvelteKit, já coberto
- [x] MT-1 — [Aplicação desktop Tauri 2: comandos, estado e permissões](../skills/stack/criar-app-tauri/SKILL.md)
- [x] MT-4 — [Instalação guiada, `--doctor` e portabilidade macOS/Windows](../docs/adr/0014-instalacao-guiada-e-portabilidade.md)
- [x] MT-9 — [Laço de correção com tentativas contadas, sem score](../skills/laco-de-correcao/SKILL.md)

## Recusados

Conceito avaliado e decidido como fora, com arquivo próprio e condição de reabertura escrita.
Separado de **Abandonados** pela ADR 0019: abandonado é o que ninguém levou adiante; recusado é
o que foi decidido que não se faz. Confundir os dois é o que faz recusa voltar como proposta
nova.

- [~] [pacote de terceiro como skill](recusados/pacote-de-terceiro-como-skill.md) — motivo: a capacidade é a API de um pacote, não lacuna do acervo; adotar pacote é decisão de stack
- [~] [guarda de comando por substring, sem ressalva de leitura](recusados/guarda-de-comando-por-substring-sem-ressalva.md) — motivo: recusa a menção junto com a execução, e impede ler as regras que ela aplica
- [~] [flag de harness como mecanismo de invocação](recusados/flag-de-harness-como-mecanismo.md) — motivo: acopla governança a um harness; três de cinco degradariam em silêncio
- [~] [spec dentro da ADR](recusados/spec-dentro-da-adr.md) — motivo: ciclos de vida opostos — a ADR é permanente, a spec se esgota

## Abandonados

_(nenhum)_
