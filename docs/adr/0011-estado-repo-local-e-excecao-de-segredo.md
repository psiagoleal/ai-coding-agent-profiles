<!-- Caminho relativo: docs/adr/0011-estado-repo-local-e-excecao-de-segredo.md -->

# ADR 0011: Estado de skill é repo-local; segredo é a única exceção

- **Status:** Accepted
- **Data:** 2026-09-11
- **Decisores:** Iago Leal (mantenedor), com Claude Code
- **Tags:** skills, portabilidade, confidencialidade, interoperabilidade

## Contexto

A biblioteca não tinha regra sobre **onde uma skill pode gravar**. Na prática cada skill
decidiu sozinha, e o resultado divergiu: `dominio/aula-audio` criava venv e vozes em
`~/.local/share/`, `dominio/mockup-lab` guarda a sessão do Penpot em `~/.config/`,
`delegacao-litellm` lê `~/.agentry/credentials.json`, e o `skills/README.md` oferecia
instalar a biblioteca inteira em `~/.claude/skills/`.

Dois insumos externos convergiram para o mesmo ponto:

1. Um **harness de terceiro** analisado em 2026-09-11 adota como don't
   universal: *"Skill, subagent ou script não lê nem grava em `~/` (config, cache,
   aprovação, estado). Override de path via variáveis de ambiente."*
2. O projeto irmão **`agentry`** já decidiu o mesmo por conta própria na sua ADR-0017:
   o estado vive em `<raiz>/.agentry/`, *"nunca num diretório global do usuário
   (`~/.config`, `~/.cache`, `~/.agentry` etc.) como localização primária"*.

O custo de não ter a regra é concreto: estado fora do repositório não é revisável, não
viaja com o `git clone`, não é reproduzível em CI, e cria acoplamento invisível entre
projetos que deveriam ser independentes.

## Decisão

> **Estado de skill é repo-local por padrão. Segredo é a única exceção.**

### 1. Repo-local por padrão
Cache, índice, venv, artefato baixado, aprovação, log e configuração de skill vivem
**dentro do repositório**. O caminho padrão é derivado da raiz do repositório, nunca do
diretório do usuário.

### 2. Todo caminho é sobrescrevível por variável de ambiente
O compartilhamento entre projetos continua possível — como **opt-in explícito**, nunca
como padrão. Download grande e imutável (pesos de modelo, vozes de TTS) é o caso típico:
`AULA_AUDIO_TTS_DIR` aponta para um caminho comum quando o usuário quer.

### 3. Segredo é exceção, e é obrigatória
Credencial, token e sessão (cookies) **não** são repo-local. Aplicar a regra ao pé da
letra os empurraria para dentro da árvore versionada, onde mais cedo ou mais tarde
seriam commitados. Segredo mora fora do repositório — `~/.agentry/credentials.json`,
`~/.config/<skill>/<sessão>` — com permissões restritas e menção explícita na skill de
que aquele caminho é exceção consciente.

Esta é a nossa divergência deliberada daquele harness: a regra dele é absoluta; a nossa
distingue **estado** de **segredo**, porque tratá-los igual degrada a confidencialidade
(ver `secrets-guard`).

### 4. O artefato que não é repo-local precisa ser ignorado
Caminho repo-local de cache entra no `.gitignore` do projeto. A skill declara isso na
sua Definição de Pronto; não é responsabilidade do usuário lembrar.

### 5. A biblioteca não se instala no diretório do usuário
Fica retirada a opção de instalar `skills/` em `~/.claude/skills/`. Cada repositório
carrega o seu acervo, versionado e revisável junto do código — coerente com o modelo de
fonte neutra + adaptador por agente do `skills/README.md`.

## Consequências

**Positivas.** Estado revisável e versionável junto do código; `git clone` traz o
projeto inteiro; CI reproduz sem preparar o `$HOME`; projetos param de compartilhar
estado por acidente; alinhamento com `agentry` (ADR-0017) e com aquele harness, o que facilita
a interoperação futura.

**Negativas.** Download grande é repetido por projeto quando o usuário não configura a
variável de ambiente — custo real de disco, mitigado pela documentação do opt-in na
própria skill. Skills existentes precisaram ser revisadas uma a uma.

**Neutras.** A regra não diz nada sobre onde o *harness* guarda o estado dele — só sobre
o que a skill e seus scripts fazem.

## Conformidade

- `dominio/aula-audio` (hoje em biblioteca privada, ADR 0013) — corrigida: padrão `<raiz>/.cache/aula-audio-tts/`, com
  `AULA_AUDIO_TTS_DIR` como opt-in e `.cache/` no `.gitignore`.
- `dominio/mockup-lab` — exceção §3 (sessão do Penpot é credencial), agora declarada
  como exceção consciente no corpo da skill.
- `delegacao-litellm` — exceção §3 (credencial do gateway). Sem mudança.
- `skills/README.md` — instalação pessoal em `~/.claude/skills/` removida (§5).
