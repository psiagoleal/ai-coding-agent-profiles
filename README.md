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
`--skills <lista>`, `--neutral-dir <nome>`, `--config <arquivo>`, `--force`, `--dry-run`.
Veja `--help`.

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
3. Ajuste as seções "Comandos exatos" e "Estrutura de diretórios" do `AGENTS.md` ao projeto.
4. Confirme `.gitignore`/`.claudeignore` cobrindo `.env` e dados sensíveis.

## Procedência

- Base conceitual: boas práticas consolidadas de uso de agentes de IA no desenvolvimento
  (OWASP Top 10 para LLM, NIST AI RMF e padrões de `AGENTS.md`/ADRs/Skills).
- Preferências de ambiente, linguagens, Doxygen e formatadores refletem o estilo do autor;
  a seção "Apoie" existe apenas no perfil pessoal e é parametrizável via `config.toml`.
