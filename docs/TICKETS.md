<!-- Caminho relativo: docs/TICKETS.md -->

# Tickets

Uma linha por ticket: identificador, link para o detalhe e uma frase. O detalhe mora no
destino do link (skill `micro-ticket-planner`).

## Em aberto

Os MT-22 a MT-37 saíram de uma análise comparativa de harness, em duas rodadas, e estão em
ordem de execução: instrumentar antes de mudar comportamento, porque mudança sem linha de base
não é refutável. O caminho crítico é MT-22 → MT-25 → MT-26. MT-24 não espera ninguém: é furo
já publicado.

- [ ] [MT-24](tickets/MT-24.md) — Hook de git em camadas: 8 de 10 formas de indireção passam hoje
- [ ] [MT-22](tickets/MT-22.md) — Colhedor retroativo de métricas de sessão (linha de base do passado)
- [ ] [MT-23](tickets/MT-23.md) — Relatório de métricas com comparação antes/depois
- [ ] [MT-25](tickets/MT-25.md) — Executor de gates: a skill de conclusão não tem script
- [ ] [MT-26](tickets/MT-26.md) — Lint do próprio `EXPECT`, com corpus de validação
- [ ] [MT-27](tickets/MT-27.md) — Enumerar skills sem `node_modules`, com teste
- [ ] [MT-28](tickets/MT-28.md) — Diagnóstico detecta placeholder não substituído
- [ ] [MT-29](tickets/MT-29.md) — Fronteira negativa nas descrições de skill, com lint
- [ ] [MT-33](tickets/MT-33.md) — Cliente único para delegação a modelo externo
- [ ] [MT-35](tickets/MT-35.md) — Roteamento validado das skills de delegação
- [ ] [MT-36](tickets/MT-36.md) — ADR do hook que recusa, e resolver a ADR 0009
- [ ] [MT-30](tickets/MT-30.md) — Pin de procedência para fonte externa de skills
- [ ] [MT-34](tickets/MT-34.md) — Sonda de capacidade de modelo e protocolo de escolha
- [ ] [MT-31](tickets/MT-31.md) — Mover o catálogo de skills do arquivo de regra para o índice
- [ ] [MT-32](tickets/MT-32.md) — Relocar segurança e fluxo: detalhe para a skill, fluxo para tabela
- [ ] [MT-37](tickets/MT-37.md) — Resolver a sobreposição entre as duas skills de fan-out
- [ ] [MT-2](tickets/MT-2.md) — Skill de núcleo de cálculo C++/CMake: 5 repositórios, nenhum coberto
- [ ] [MT-3](tickets/MT-3.md) — Skill de biblioteca/CLI em Rust: 8 repositórios com `Cargo.toml`
- [ ] [MT-6](tickets/MT-6.md) — Propagar às instalações de `~/dev` — adiado pelo autor: cada repositório é atualizado quando a árvore estiver limpa
- [ ] [MT-21](tickets/MT-21.md) — Contraparte da adoção de papéis: declarar dependência de harness e verificar
- [ ] [MT-20](tickets/MT-20.md) — Decisão tipada como camada de roteamento — bloqueado por medição no `agentry`
- [ ] [MT-15](tickets/MT-15.md) — Provas adversariais executáveis nas skills de segurança e serviço
- [ ] [MT-16](tickets/MT-16.md) — Ledger de evidência com impressão digital e validade
- [ ] [MT-17](tickets/MT-17.md) — Skill `exercitar-skill`: derivar as racionalizações de observação
- [ ] [MT-18](tickets/MT-18.md) — Skill de disciplina de aprendizado de máquina (anti-vazamento)
- [ ] [MT-14](../docs/adr/0015-biblioteca-privada-em-repositorio-publico.md) — Decidir a ADR 0015: biblioteca privada em repositório público
- [ ] [MT-7](tickets/MT-7.md) — Medir a nossa verificação contra o laço com score, em gabarito comum
- [ ] [MT-12](tickets/MT-12.md) — UI React: só se a empresa fechar React em vez de Svelte (decisão pendente)

## Concluídos

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

## Abandonados

_(nenhum)_
