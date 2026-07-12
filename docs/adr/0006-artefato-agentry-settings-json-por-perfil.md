<!-- Caminho relativo: docs/adr/0006-artefato-agentry-settings-json-por-perfil.md -->

# ADR 0006: Distribuição de `.agentry/agentry.settings.json` por perfil

- **Status:** Proposed <!-- pendente de validação de implementação antes de Accepted -->
- **Data:** 2026-07-12
- **Decisores:** Equipe técnica
- **Tags:** interop, agentry, settings-schema, jq, overlay

## Contexto

O contrato de interoperabilidade com o `agentry` (`docs/interop/SPEC.md`, canônico neste
repositório) previa, desde a ADR-0003 daquele repo, que o `agentry` consumisse um
`settings-schema:1` a partir de `.claude/settings.json`. Na prática, esse artefato é o
formato **nativo do Claude Code** (`env`, `permissions.deny`/`ask` como padrões
`"Bash(...)"`) — domínio incompatível com o que o `agentry` de fato precisa (roteamento por
`task-class`, seleção de provider, permissões por **nome exato de tool**, flags de
contexto/Reviewer). O `agentry` registrou essa investigação e a decisão correspondente na
**ADR-0018** daquele repositório (`agentry/docs/adr/0018-artefato-e-schema-minimo-de-
configuracao-do-agentry.md`): um artefato próprio, `.agentry/agentry.settings.json`, cujo
**schema** é de propriedade do lado executor (`agentry`) — este repositório só distribui
**valores *default* por perfil**, exatamente como já faz hoje para `.claude/settings.json`.

Charter já estabelecido (`SPEC.md` §1): `profiles` define política, `agentry` executa. O
schema é responsabilidade de quem consome (`agentry`); este ADR só decide **como** este
repositório passa a distribuir o artefato.

## Decisão

1. **Três arquivos novos, um por perfil**, seguindo a primeira fatia de schema congelada pela
   ADR-0018 do `agentry`:
   - `profiles/empresa/.agentry/agentry.settings.json`
   - `profiles/externo-confidencial/.agentry/agentry.settings.json`
   - `profiles/pessoal/.agentry/agentry.settings.json`

   Cada um com `permissions.deny`/`ask` (nomes exatos de tool do `agentry`, nunca padrões
   Bash) e as 4 *flags* de contexto/provider já congeladas — valores diferenciados por
   perfil na mesma lógica já usada em `.claude/settings.json` (`empresa` mais conservador em
   `deny`).

2. **`.agentry/.gitignore` também distribuído** por perfil, com o mesmo conteúdo que
   `state_dir::ensure_state_dir` (`agentry`, MT-38/ADR-0017 emendada) geraria — `*` +
   exceção nomeada para `agentry.settings.json`. Garante que o repositório-alvo já nasce com
   o resto de `.agentry/` corretamente ignorado, mesmo antes da primeira execução do
   `agentry` (que só cria o `.gitignore` se ainda não existir).

3. **Classificação em `scripts/setup-profile.sh`:** uma linha nova em `bucket_for()` —
   `.agentry/agentry.settings.json)  echo hybrid_json ;;` — reaproveitando
   `update_json_settings()` (já genérica, não hardcoded para `.claude/settings.json`) para
   *deep-merge* via `jq` em `--update` (regra vence conflito, customização do usuário
   sobrevive). `.agentry/.gitignore` cai no balde padrão (`rule`, sempre sobrescrito —
   conteúdo determinístico, não é para o usuário editar à mão). **Nenhuma outra mudança de
   descoberta é necessária**: o laço principal (`find "$PROFILE_SRC" -type f`) já enumera
   qualquer arquivo novo sob a pasta do perfil automaticamente.

4. **`docs/interop/SPEC.md`** (canônico neste repositório) ganha uma linha na tabela de
   artefatos (§2): `.agentry/agentry.settings.json` | `agentry-settings-schema:1` | *(rascunho
   — ADR-0018 @ agentry)*. Versão do contrato de interoperabilidade continua `1` — mudança
   aditiva (novo artefato), não incompatível (SPEC §4).

## Consequências

- **Impacto positivo:** o `agentry` passa a poder ser configurado de verdade por perfil, sem
  reinterpretar um formato alheio (`.claude/settings.json`); reaproveita a disciplina de
  `--update` não-destrutivo já validada em produção para `.claude/settings.json`; nenhuma
  mudança na lógica central de `setup-profile.sh` além de uma linha em `bucket_for()`.
- **Impacto negativo:** mais um arquivo por perfil para manter em sincronia com o schema do
  `agentry` — se a ADR-0018 evoluir (novas fatias de schema), os três arquivos precisam de
  atualização manual coordenada; nenhuma automação de sincronia entre os dois repos existe
  hoje além do `exchange-log.md`.
- **Trade-offs aceitos:** o schema em si não é validado estruturalmente por este repositório
  (sem JSON Schema formal ainda) — confiança na disciplina de registrar cada extensão no
  `exchange-log.md` do `agentry` antes de editar os três arquivos aqui.

## Diretriz de Conformidade de Código

- **Proibido:** este repositório inventar chaves de schema não congeladas por uma ADR do
  `agentry` (o schema é de propriedade do lado executor); usar padrões Bash em
  `permissions.deny`/`ask` de `agentry.settings.json` (domínio incompatível, ver ADR-0018 @
  `agentry`); versionar segredo/endpoint real nos três arquivos `agentry.settings.json`
  (mesma regra já aplicada a `.claude/settings.json`).
- **Obrigatório:** manter os três arquivos por perfil sincronizados com a fatia de schema
  atual da ADR-0018 (@ `agentry`); classificar `agentry.settings.json` como `hybrid_json` em
  `bucket_for()`; toda extensão futura de schema é primeiro registrada no `exchange-log.md`
  do `agentry`, só depois refletida aqui.

> Qualquer desvio desta regra viola as diretrizes de conformidade arquitetural do projeto
> e deve ser reportado para revisão antes de prosseguir.

## Referências

- ADR-0018 (`agentry`): `agentry/docs/adr/0018-artefato-e-schema-minimo-de-configuracao-do-agentry.md`
- ADR-0017 emendada (`agentry`): `agentry/docs/adr/0017-diretorio-de-estado-local-do-agente.md`
- Entrada correspondente no `exchange-log.md` (canônico em `agentry`):
  "2026-07-12 — Sétima extensão ao `settings-schema:1`"
- Classificação de baldes / `update_json_settings()`: `scripts/setup-profile.sh:133-140,244-257`
