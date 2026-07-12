<!-- Caminho relativo: docs/CURRENT-STATE.md -->

# Estado Corrente (Handoff) — Framework

> Fonte central de sincronização entre turnos. Atualizado a cada commit. Não inclua segredos.
> Mantido conforme a skill `handoff-updater`.

## Último turno

- **Data:** 2026-07-12
- **Branch:** `main`
- **Commit:** `(pendente — ver histórico abaixo após commit)`
- **Autor do turno:** Iago Leal (mantenedor), com Claude Code

## Metas cumpridas neste turno

- [x] **ADR 0006** — Distribuição de `.agentry/agentry.settings.json` por perfil —
      registrado como `Proposed`. Fecha, do lado deste repositório, o loop do
      `settings-schema:1` que ficou pendente desde o bootstrap do ecossistema (ver
      `docs/interop/exchange-log.md` no `agentry` — sétima extensão, 2026-07-12): o artefato
      que existia até então (`.claude/settings.json`) é o formato **nativo do Claude Code**,
      incompatível por design com o que o `agentry` de fato consome (nomes exatos de tool,
      não padrões Bash). O schema em si é de propriedade do `agentry` (ADR-0018 daquele
      repo); este repositório só distribui valores *default* por perfil.
- [x] Três arquivos novos por perfil (`empresa`/`externo-confidencial`/`pessoal`):
      `.agentry/agentry.settings.json` (primeira fatia de schema: `permissions.deny`/`ask` +
      4 *flags* de contexto/provider) e `.agentry/.gitignore` (mesmo conteúdo que o
      `agentry` geraria sozinho — `*` + exceção nomeada para o arquivo de config).
- [x] `scripts/setup-profile.sh`: `bucket_for()` ganha `.agentry/agentry.settings.json` como
      `hybrid_json` — testado com `--dry-run` real (descoberta automática funcionou sem
      nenhuma outra mudança) e com `--update --dry-run` (confirmado: `.gitignore` vira
      `rule` sobrescrito, `agentry.settings.json` vira `mesclaria (jq)`).
- [x] `docs/interop/SPEC.md` (canônico deste repo) ganha a linha do novo artefato na tabela
      de §2; "Última atualização" avançada para 2026-07-12.

## Em andamento

- [ ] ADRs 0001–0006 estão `Proposed`. Os **0003–0006** só devem ser promovidos a `Accepted`
      após a **validação de implementação** descrita na Diretriz de Conformidade de cada um
      — para 0006, isso é o `agentry` de fato consumir o arquivo (MT-39/MT-40 daquele repo,
      `docs/roadmap-v0.2.md`).
- [ ] 0001 (RTK) e 0002 (OKF) seguem pendentes da reanálise de maturidade (inalterado desde
      2026-06-19 — tema independente do settings-schema, não tocado nesta sessão).
- [ ] ADRs 0003–0005 (perfis base+overlay, skills executáveis, config de serviços) seguem
      **não implementados** — inalterado desde 2026-06-19, tema independente.

## Impedimentos técnicos abertos

- Implementação dos ADRs 0003–0005 **não iniciada** — depende do refactor central do
  `setup-profile.sh` (separar núcleo de merge da política de instalação/`--dry-run`).
- Decisão de adoção de RTK e OKF **bloqueada** aguardando reanálise de maturidade das fontes.
- ADR 0006 depende de MT-39/MT-40 no `agentry` para ser validada de ponta a ponta antes de
  promover a `Accepted`.

## Próximo passo sugerido

**Curto prazo:** acompanhar o `agentry` implementar MT-39 (`Settings::from_file`) e MT-40
(consumo real das 4 flags) — quando isso acontecer, validar os três `agentry.settings.json`
contra um `agentry` de verdade antes de promover a ADR 0006 a `Accepted`.

**Retomando o trabalho anterior (inalterado desde 2026-06-19) — Implementação dos ADRs
0003–0005**, em sessão dedicada, seguir o plano aprovado
(`~/.claude/plans/unified-booping-parasol.md`). Ordem sugerida:

1. Refatorar `setup-profile.sh`: extrair `merge_text`/`merge_json` puros (sem `--dry-run`),
   parametrizar mensageria de órfãos, adicionar `trap` de cleanup.
2. Descoberta dinâmica de perfis + resolução de diretório externo (`--profiles-dir`,
   `AGENTIC_PROFILES_DIR`, `[profiles].overlay_dir`) + leitura de `extends` com detecção de ciclo.
3. Estágio de composição base+overlay reusando os núcleos de merge.
4. Seção `[services]` no `config.toml` (chave global única) + injeção via `jq` no `settings.json`.
5. Skill de referência `skills/web-search/` (searxng) + cobertura de overlay-skills no adaptador.
6. Endurecer `deny`/`ask` por perfil (execução de script e egress) conforme ADR 0004.

Validar conforme a seção "Verificação" do plano. Só então atualizar "Decisão"/"Consequências"
de cada ADR e, se aprovado, promover a `Accepted`.

### Reanálise pendente (turnos anteriores)

**Reanálise de maturidade e avaliação para implementação** — em sessão dedicada, revalidar os
links de referência e preencher cada ADR antes de qualquer promoção a `Accepted`:

**ADR 0001 — RTK** (`docs/adr/0001-adocao-de-rtk-para-reducao-de-tokens.md`):
- <https://github.com/rtk-ai/rtk>
- <https://github.com/rtk-ai/rtk/blob/master/CONTRIBUTING.md>
- Avaliar: idade real do projeto e cadência de releases; política de versionamento; volume e
  qualidade de issues/CVEs; comportamento da truncagem em comandos sensíveis (segurança/
  auditoria); fixar uma versão homologada; confirmar ausência de acesso à rede pelo binário.

**ADR 0002 — OKF / LLM-Wiki** (`docs/adr/0002-adocao-de-okf-llm-wiki-para-conhecimento-estruturado.md`):
- <https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/>
- <https://github.com/GoogleCloudPlatform/knowledge-catalog>
- <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
- Avaliar: estabilidade da spec OKF v0.1 (mudanças entre versões); campos efetivamente
  obrigatórios; delta concreto entre o frontmatter atual (memória/ADR/handoff) e o do OKF;
  viabilidade de uma skill `knowledge-curator` (ingest/query/lint) sem acoplar a tooling
  proprietário (ex.: Knowledge Catalog).

Após a reanálise: atualizar a seção "Decisão"/"Consequências" de cada ADR, decidir o escopo
por perfil e, se aprovado, promover a `Accepted` e abrir os micro-tickets de implementação.

---

## Histórico (mais recente no topo)

| Data | Commit | Resumo | MT |
|------|--------|--------|----|
| 2026-07-12 | `(pendente)` | ADR 0006 (`.agentry/agentry.settings.json` por perfil); 3 arquivos novos por perfil + `.gitignore`; `setup-profile.sh` (`bucket_for`) + `SPEC.md` atualizados; fecha o loop do settings-schema do lado deste repo | — |
| 2026-06-19 | `(pendente)` | ADRs 0003 (perfis base+overlay), 0004 (skills executáveis) e 0005 (config de serviços + skills overlay) como `Proposed`; design e casos de borda travados, implementação pendente | — |
| 2026-06-15 | `(pendente)` | Estrutura de ADRs do framework + ADR 0001 (RTK) e 0002 (OKF) como `Proposed`; handoff com reanálise de maturidade pendente | — |
