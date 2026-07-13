<!-- Caminho relativo: README.md -->

# Framework de Configuração e Regramento de Agentes de IA

Documentação operacional para configuração, alinhamento, regramento e definições de
agentes de IA no desenvolvimento de software. Consolida boas práticas de uso de agentes
de codificação em artefatos prontos para uso, em **três perfis** e em **duas formas
complementares** (arquivos de instrução tradicionais + Skills).

## Perfis

| Perfil | Para quem | Confidencialidade |
|--------|-----------|-------------------|
| [`profiles/empresa`](profiles/empresa/AGENTS.md) | Profissional dentro da empresa, projetos corporativos | **Crítica** |
| [`profiles/externo-confidencial`](profiles/externo-confidencial/AGENTS.md) | Profissional fora da empresa, projetos de cliente sob NDA | **Alta** |
| [`profiles/pessoal`](profiles/pessoal/AGENTS.md) | Projetos pessoais open-source | Relaxada |

Para escolher e comparar, veja [`docs/comparativo-perfis.md`](docs/comparativo-perfis.md).

## Duas formas de documentação

1. **Tradicional (instruções gerais):** cada perfil tem um `AGENTS.md` como **fonte única
   da verdade**; `CLAUDE.md`, `.cursorrules` e `.github/copilot-instructions.md` são
   ponteiros finos para ele. Inclui `.claude/settings.json`, `.claudeignore`, `.env.example`
   e templates de `docs/CURRENT-STATE.md` e `docs/adr/`.
2. **Skills (modular):** biblioteca de Skills de governança em [`skills/`](skills/README.md),
   com *progressive disclosure* — carregadas só quando a tarefa as aciona. A biblioteca é
   **independente de agente**: a pasta neutra `skills/` é a fonte da verdade; adaptadores
   por agente (ex.: `.claude/skills/`) são apenas ponteiros gerados pelo script.

## Script de instalação

[`scripts/setup-profile.sh`](scripts/setup-profile.sh) copia um perfil para um repositório
alvo e gerencia as skills (pasta neutra + adaptador de agente):

```bash
scripts/setup-profile.sh <perfil> <repo-alvo> [opções]

# exemplos
scripts/setup-profile.sh empresa ~/dev/meu-projeto                 # symlinks (padrão)
scripts/setup-profile.sh pessoal ~/dev/oss --skills-mode copy      # cópias (Windows)
scripts/setup-profile.sh empresa ./alvo --dry-run                  # simula, não escreve
scripts/setup-profile.sh externo-confidencial ./x --skills secrets-guard,pr-review-guard
```

Opções principais: `--skills-mode {symlink|copy|none}`, `--agent {claude|none}`,
`--skills <lista>`, `--neutral-dir <nome>`, `--config <arquivo>`, `--update`, `--force`,
`--dry-run`. Veja `--help`.

## Atualização não-destrutiva (`--update`)

Para atualizar as **regras** de um repositório já configurado **sem apagar nem sobrescrever
os arquivos vivos** do projeto (ADRs, `CURRENT-STATE.md`, `.env`), use `--update`:

```bash
scripts/setup-profile.sh empresa ~/dev/meu-projeto --update --dry-run   # mostra o plano
scripts/setup-profile.sh empresa ~/dev/meu-projeto --update             # aplica
```

Em `--update`, cada arquivo é classificado em três baldes:

| Balde | Arquivos | Ação |
|-------|----------|------|
| **Regra / ponteiro** | `CLAUDE.md`, `.cursorrules`, `copilot-instructions.md`, biblioteca `skills/` | sobrescrito (a regra vence) |
| **Híbrido** | `AGENTS.md`, `.claudeignore`, `.env.example` (texto) e `.claude/settings.json` (JSON) | **merge** preservando o que é do projeto |
| **Vivo** | `docs/CURRENT-STATE.md`, `docs/adr/NNNN-*.md`, `.env` | **nunca tocado** |

Arquivos novos (ausentes no alvo) são sempre criados. **Nada é apagado.** Revise sempre com
`git diff` no alvo (de preferência com a árvore limpa antes de rodar).

### Marcadores `USER:*` nos híbridos de texto

Nos híbridos de texto, os trechos **específicos do projeto** ficam entre marcadores de ID
estável — comentário invisível em Markdown, `#` em `.claudeignore`/`.env.example`:

```markdown
<!-- USER:BEGIN id=comandos-exatos -->
```bash
# seus comandos reais — preservados em todo --update
```
<!-- USER:END -->
```

No update, o miolo entre `USER:BEGIN id=X` e `USER:END` é **preservado** e reinjetado por
ID; todo o resto é regenerado a partir do template (assim, regras novas aparecem sozinhas).
Edite **dentro** dessas ilhas para que suas mudanças sobrevivam. Casos de borda tratados:

- **Bloco órfão** (um ID que saiu do template) é preservado ao final como `USER:ORPHAN` + aviso.
- **Híbrido legado sem marcadores** não é sobrescrito: gera-se um `<arquivo>.new` ao lado.

### Requisito: `jq`

O merge do `.claude/settings.json` (JSON, sem comentários) usa **`jq`** (`sudo apt install jq`):
as chaves do framework vencem em conflito, mas chaves extras suas são preservadas. O `jq` só
é exigido quando o `--update` precisa mesclar o `settings.json`.

## Configuração pessoal (`config.toml`)

Os arquivos do perfil pessoal usam placeholders `{{...}}` (nome do autor, ano de copyright,
canal de apoio) para **não fixar a identidade de uma pessoa** no template. Cada usuário
define os seus dados em um `config.toml` local (não versionado):

```bash
cp config.example.toml config.toml   # ajuste author_name, copyright_year e o canal de apoio
```

Ao rodar o `setup-profile.sh`, o script lê o `config.toml` (ou, na ausência dele, o
`config.example.toml`) e substitui os placeholders `{{AUTHOR_NAME}}`, `{{COPYRIGHT_YEAR}}`,
`{{SUPPORT_LABEL}}` e `{{SUPPORT_URL}}` nos arquivos copiados para o repositório alvo.

## Estrutura

```
README.md
config.example.toml            # modelo de configuração pessoal (copie para config.toml)
docs/
  comparativo-perfis.md        # matriz de diferenças entre perfis
profiles/
  empresa/  externo-confidencial/  pessoal/
    AGENTS.md  CLAUDE.md  .cursorrules  .github/copilot-instructions.md
    .claudeignore  .env.example  .claude/{settings.json,skills/}
    docs/{CURRENT-STATE.md, adr/}
skills/                        # biblioteca neutra (independente de agente)
  secrets-guard/  adr-writer/  micro-ticket-planner/
  handoff-updater/  pr-review-guard/
scripts/
  setup-profile.sh             # instala um perfil + skills num repo alvo
```

## Como usar em um projeto real

1. Escolha o perfil ([`docs/comparativo-perfis.md`](docs/comparativo-perfis.md)).
2. Rode o script: `scripts/setup-profile.sh <perfil> <repo-alvo>` — ele copia o perfil, a
   biblioteca neutra de skills e gera o adaptador `.claude/skills/`.
3. Ajuste as seções "Comandos exatos" e "Estrutura de diretórios" do `AGENTS.md` ao projeto
   — edite **dentro** dos marcadores `USER:BEGIN/END` para que `--update` preserve as mudanças.
4. Confirme `.gitignore`/`.claudeignore` cobrindo `.env` e dados sensíveis.

## Interoperabilidade

Este framework (**camada de política**) faz par com o projeto irmão `agentry` (**motor de
execução** agêntico em Rust), que lê estes artefatos e os **impõe** (controle de egresso,
permissões, skills). O contrato entre os dois é versionado e canônico aqui:

- **Contrato (fonte da verdade):** [`docs/interop/SPEC.md`](docs/interop/SPEC.md) — charter de
  responsabilidades + esquema dos artefatos + taxonomia de privacidade (perfil → classe de egresso).
- **Trocas entre os projetos:** registradas no `exchange-log` append-only do lado executor
  (`agentry/docs/interop/exchange-log.md`); decisões vinculantes viram ADR no repo dono.

Regra: este repo **define** política; `agentry` **executa**. Não duplicar execução aqui nem
política lá.

## Procedência

- Base conceitual: boas práticas consolidadas de uso de agentes de IA no desenvolvimento
  (OWASP Top 10 para LLM, NIST AI RMF e padrões de `AGENTS.md`/ADRs/Skills).
- Preferências de ambiente, linguagens, Doxygen e formatadores refletem o estilo do autor;
  a seção "Apoie" existe apenas no perfil pessoal e é parametrizável via `config.toml`.
