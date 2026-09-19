<!-- Caminho relativo: docs/CURRENT-STATE.md -->

# Estado Corrente (Handoff) — Framework

> Fonte central de sincronização entre turnos. Atualizado a cada commit. Não inclua segredos.
> Mantido conforme a skill `handoff-updater`.

## Último turno

- **Data:** 2026-09-17
- **Branch:** `main`
- **Commit:** `(pendente — nada commitado desde 828c978)`
- **Autor do turno:** Iago Leal (mantenedor), com Claude Code

## Metas cumpridas neste turno

1. **22 repositórios de `~/dev` atualizados** com `--update --agent claude,agentry
   --agents auto`, perfil detectado do `AGENTS.md` de cada um. Todos com `exit=0`.
   - **Repos públicos** (`agentry`, `atldp`, `docling_service`, `neocad`) receberam **só a
     biblioteca pública** (14 skills, 0 subagents), via `--config` sem `fontes_extras` —
     material de terceiros não entra em repositório público. Verificado com o verificador de
     vazamento em cada um.
   - Os demais receberam 17 skills + os subagents citados por elas (`--agents auto`).
   - **7 repositórios não são git**: como não havia linha de base nem `git diff` para
     reverter, cada um recebeu antes um `.backup-framework-<data>.tar.gz`.
   - Todos passam a ter `.agent-profile/baseline.sha256`: da próxima vez, edição local fora
     das ilhas para de ser sobrescrita em silêncio.
2. **Gateway OpenAI-compatible configurado no nível da máquina**, não nos repositórios:
   `~/.agentry/agentry.settings.json` (ADR-0038 do `agentry`) com `providers.litellm` e a
   task-class `delegada`. O endereço do gateway **não** é versionado em repositório nenhum; a
   chave continua vindo de variável de ambiente.
3. **Fronteira de precedência acordada com o `agentry`** registrada em
   `docs/interop/portabilidade.md`; instalador passou a remover adaptador vazio e avisar.

## Em andamento (herdado, inalterado)

- [ ] ADRs 0001–0006 seguem `Proposed`. 0003–0006 só viram `Accepted` após a validação de
      implementação da Diretriz de Conformidade de cada um — para a 0006, isso é o `agentry`
      de fato consumir o arquivo (MT-39/MT-40 daquele repo).
- [ ] 0001 (RTK) e 0002 (OKF) pendentes da reanálise de maturidade (desde 2026-06-19).
- [ ] ADRs 0003–0005 (perfis base+overlay, skills executáveis, config de serviços)
      **não implementados** — depende do refactor central do `setup-profile.sh`
      (separar núcleo de merge da política de instalação/`--dry-run`).

> Rodadas encerradas: [`docs/handoff-arquivo.md`](handoff-arquivo.md).

## Impedimentos abertos

- **Delegação ao gateway pelo `agentry` está bloqueada por desenho**, aguardando decisão do
  mantenedor: declarei `egressClass: cloud-ok` porque o roteamento efetivo dos backends não
  foi confirmado por quem opera o gateway. Sob esse valor, toda sessão com perfil restritivo
  descarta o candidato e cai no Ollama — foi o que os testes mostraram. Se o gateway serve
  modelos hospedados internamente, o valor correto é `local-only` em
  `~/.agentry/agentry.settings.json`. A rota direta (`oa-chat`) **não** depende disso e já
  funciona de dentro dos repositórios.
- **Vazamento em repositório público de terceiro:** `agentry` (público) cita o nome do harness
  corporativo em `docs/handoff-arquivo.md:109`, commit `cf9c268`, já publicado no branch
  `origin/chore/build-linux-e-higiene-de-disco`. Não está em `main`. A sessão daquele projeto
  foi avisada; a decisão sobre o histórico é do mantenedor.

## Próximo passo

1. Exercitar os adaptadores gerados **ao vivo** nas CLIs (`codex debug prompt-input`,
   `opencode agent list`) — hoje a prova é de gramática e parsing, não de carga real.
2. Gerador para Gemini e Copilot — mesmo script, ramo novo.
3. Revisar menções a `CLAUDE.md` e usos de tool de subagent nos corpos (portabilidade).
4. Reclassificar as skills de domínio antigas com migração para instalações existentes.
5. O hook de pre-commit é **local**: reinstalar em cada clone novo deste repositório.

## Ação pendente fora deste repositório

`agentry` (solicitado à sessão do projeto em 2026-09-17): descobrir skills em `.agents/skills/`
além de `.claude/skills/`, por precedência sem merge (ADRs 0020/0023 dele). Roadmap, só
informado: subagent por papel nomeado, além do despacho por `task_class`.

> Rodadas encerradas e tabela de commits: [`docs/handoff-arquivo.md`](handoff-arquivo.md).
