<!-- Caminho relativo: docs/handoff-arquivo.md -->

# Handoff — Arquivo Histórico

> Rodadas encerradas, append-only. O estado corrente vive em
> [`docs/CURRENT-STATE.md`](CURRENT-STATE.md), que aponta para cá.
> Mantido conforme a skill `handoff-updater`.

## Rodada de 2026-07-12 — ADR 0006 e settings por perfil

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


## Histórico (mais recente no topo)

| Data | Commit | Resumo | MT |
|------|--------|--------|----|
| 2026-09-17 | `(pendente)` | `delegacao-openai-compat`+`oa-chat`; ADR 0013 (taxonomia, subagents, bibliotecas múltiplas, portabilidade); separação público × privado; `--agents`/`--fonte`/seleção por categoria; linha de base anti-perda no `--update`; regra de trailers uniformizada | — |
| 2026-09-11 | `(pendente)` | Análise de harness de terceiro: `caveman` atualizada, `gates-de-conclusao` e `paralelizacao-em-grafo` corrigidas; ADR 0011 (estado repo-local, segredo é exceção) e ADR 0012 (adaptadores multi-harness); piloto de registro persuasivo em `secrets-guard` | — |
| 2026-08-12 | `(pendente)` | ADR 0008; balde `scaffold` (corrige sobrescrita de README/CHANGELOG/LICENSE); ilhas `ambiente-desenvolvimento`/`estilo-codificacao`/`secoes-adicionais`/`catalogo-local`; parser de marcadores só em início de linha; categoria `skills/dominio/` (`mockup-lab`, `pc-builder`); 20 projetos ressincronizados | — |
| 2026-07-12 | `(pendente)` | ADR 0006 (`.agentry/agentry.settings.json` por perfil); 3 arquivos novos por perfil + `.gitignore`; `setup-profile.sh` (`bucket_for`) + `SPEC.md` atualizados; fecha o loop do settings-schema do lado deste repo | — |
| 2026-06-19 | `(pendente)` | ADRs 0003 (perfis base+overlay), 0004 (skills executáveis) e 0005 (config de serviços + skills overlay) como `Proposed`; design e casos de borda travados, implementação pendente | — |
| 2026-06-15 | `(pendente)` | Estrutura de ADRs do framework + ADR 0001 (RTK) e 0002 (OKF) como `Proposed`; handoff com reanálise de maturidade pendente | — |
