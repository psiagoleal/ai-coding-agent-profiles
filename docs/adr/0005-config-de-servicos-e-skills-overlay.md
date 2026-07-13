<!-- Caminho relativo: docs/adr/0005-config-de-servicos-e-skills-overlay.md -->

# ADR 0005: Configuração de serviços locais e skills overlay do projeto

- **Status:** Proposed <!-- pendente de validação de implementação antes de Accepted -->
- **Data:** 2026-06-19
- **Decisores:** Equipe técnica
- **Tags:** config, toml, skills, overlay, settings-json, jq

## Contexto

O ADR 0004 introduz skills executáveis cujo endpoint vem de uma **env var** (ex.:
`SEARXNG_URL`). Falta definir **como o usuário configura** esse endpoint e **onde vivem as
skills próprias** do usuário (decidido com o usuário: *overlay no projeto-alvo*).

Hoje a configuração pessoal está em `config.toml` (`[user]`, `[support]`, 4 placeholders),
lida por `toml_get` (`setup-profile.sh:95-97`) e injetada por `apply_substitutions`/
`sed_escape_repl` (`:100`, `:103-112`). Duas características do código atual impõem cuidados:

1. `toml_get` é **cego a seção** — casa a primeira ocorrência da chave em **qualquer**
   seção. Chaves homônimas entre seções colidem.
2. `sed_escape_repl` (`:100`) escapa `& | \`, mas **não escapa aspas** — injetar uma URL via
   sed dentro do `settings.json` (JSON) pode **corromper** o arquivo.

## Decisão

> **Proposta (não ratificada).** Fica proposto (a) configurar serviços locais via nova seção
> em `config.toml` com injeção JSON-safe, e (b) suportar **skills overlay** versionadas no
> projeto-alvo, condicionado à validação descrita na Diretriz de Conformidade.

### 1. Seção `[services]` no config
Nova seção em `config.toml`/`config.example.toml` (ex.: `[services]` com `searxng_url`). O
script semeia a env var correspondente no alvo: o `config.toml` é o **default pessoal**, e o
**contrato de runtime continua sendo a env var** (ADR 0004), que o `.env` do projeto pode
sobrescrever.

### 2. Chave globalmente única (contorno do `toml_get` cego a seção)
Enquanto `toml_get` não for ciente de seção, as chaves de serviço devem ser **globalmente
únicas** (ex.: `searxng_url`, **não** `url`). Alternativa preferível: tornar `toml_get`
ciente de seção — decidir na implementação. A regra adotada deve ser documentada no
`config.example.toml`.

### 3. Injeção JSON-safe via `jq`
A injeção do endpoint em `.claude/settings.json` (bloco `env`) é feita via **`jq`**
(ex.: `.env.SEARXNG_URL = $url`), **nunca** por substituição `sed` — garante JSON válido
mesmo com caracteres especiais. Em arquivos de **texto** (`.env.example`), mantém-se a
injeção atual via `apply_substitutions`/`sed_escape_repl`.

### 4. Skills overlay do projeto
As skills próprias do usuário vivem numa **pasta de overlay no projeto-alvo**, versionadas
com o projeto. São **excluídas do `--update`** do framework (tratadas como conteúdo "vivo",
nunca sobrescritas). A geração do adaptador `.claude/skills/` deve **cobrir** as
overlay-skills — hoje o estágio 3 (`setup-profile.sh:384-407`) só itera as skills do
framework e faz `rm -rf` no destino. É **obrigatório** tratar **colisão de nome** entre uma
overlay-skill e uma skill do framework (namespacing ou detecção/erro), para que a do
framework não atropele silenciosamente a do projeto na descoberta.

## Consequências

- **Impacto positivo:** endpoints de serviços locais configuráveis num só lugar pessoal, com
  override por projeto; injeção robusta sem corromper JSON.
- **Impacto positivo:** usuário mantém skills próprias versionadas com o projeto, intocadas
  pelo `--update`.
- **Impacto negativo / trade-off aceito:** a regra de "chave globalmente única" é uma
  limitação herdada do parser; aceitável até `toml_get` virar ciente de seção.
- **Impacto negativo:** colisão de nomes entre overlay-skills e skills do framework exige
  política explícita, sob pena de descoberta ambígua no `.claude/skills/`.

## Diretriz de Conformidade de Código

- **Obrigatório:** injetar endpoints no `settings.json` via `jq`, **nunca** via `sed`.
- **Obrigatório:** usar chaves de serviço globalmente únicas no `config.toml` **ou** tornar
  `toml_get` ciente de seção; documentar a escolha no `config.example.toml`.
- **Obrigatório:** excluir as overlay-skills do `--update` (conteúdo "vivo", como
  `docs/CURRENT-STATE.md` e `.env` em `bucket_for`, `setup-profile.sh:133-140`).
- **Obrigatório:** resolver colisão de nome overlay-skill × skill-do-framework com política
  explícita (namespacing ou erro), nunca sobrescrita silenciosa do adaptador.
- **Proibido:** versionar valores reais de endpoint/credencial no repositório; o
  `config.toml` permanece pessoal e ignorado, e o `.env` real nunca é versionado.

> Qualquer desvio desta regra viola as diretrizes de conformidade arquitetural do projeto
> e deve ser reportado para revisão antes de prosseguir.

## Referências

- Parser/injeção atuais: `scripts/setup-profile.sh:95-112`
- Classificação de baldes (`live` nunca tocado): `scripts/setup-profile.sh:133-140`
- ADRs relacionados: [0003](0003-perfis-base-overlay.md) (base+overlay), [0004](0004-skills-executaveis.md) (skills executáveis)
