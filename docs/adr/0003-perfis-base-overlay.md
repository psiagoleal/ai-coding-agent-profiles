<!-- Caminho relativo: docs/adr/0003-perfis-base-overlay.md -->

# ADR 0003: Perfis em modelo base + overlay (descoberta dinâmica e composição)

- **Status:** Proposed <!-- pendente de validação de implementação antes de Accepted -->
- **Data:** 2026-06-19
- **Decisores:** Equipe técnica
- **Tags:** perfis, setup-profile, composição, merge, extensibilidade

## Contexto

O framework provê três perfis (`pessoal`, `empresa`, `externo-confidencial`) sob
`profiles/`. Na prática eles estão **engessados**:

- O `scripts/setup-profile.sh` valida o perfil apenas testando
  `[[ -d "$PROFILES_DIR/$PROFILE" ]]` (`setup-profile.sh:301-302`) e a mensagem de erro
  lista a string hardcoded `"empresa | externo-confidencial | pessoal"`.
- Não há lugar de 1ª classe para o usuário **criar perfis próprios**.
- Quem edita um perfil padrão dentro do repo do framework perde as edições no próximo
  `git pull` (conflito de árvore versionada do framework).

Queremos destravar isso **sem** abandonar os perfis-base versionados: o framework continua
dono das *regras*, e o usuário compõe/customiza por cima, num diretório que o `git pull`
do framework não toca.

O framework já possui um **motor de merge não-destrutivo** maduro no `--update`
(`setup-profile.sh:157-270`): ilhas `USER:BEGIN id=.../USER:END` em híbridos de texto,
deep-merge `jq -s '.[0]*.[1]'` em `settings.json`, e classificação por balde em
`bucket_for` (`:133-140`). Reusá-lo para compor base+overlay é o caminho de menor risco —
desde que se reconheça o descasamento semântico descrito abaixo.

## Decisão

> **Proposta (não ratificada).** Fica proposto adotar um modelo **base + overlay** de
> perfis, com **descoberta dinâmica** e **composição** que reusa o motor de merge existente,
> condicionado à validação de implementação descrita na Diretriz de Conformidade.

### 1. Fonte externa de perfis (configurável)
Diretório de perfis do usuário, resolvido por precedência:
`--profiles-dir <dir>` > env `AGENTIC_PROFILES_DIR` > `[profiles].overlay_dir` no
`config.toml`. Esse diretório **não** vive no repo do framework, então sobrevive ao
`git pull`.

### 2. Descoberta dinâmica
Substituir a validação hardcoded (`:301-302`) por uma função que lista perfis válidos de
**ambos** os diretórios (framework + externo). Marcador de validade: presença de
`AGENTS.md` e/ou do manifesto `profile.toml`. A ajuda (`--help`) e as mensagens de erro
passam a listar os perfis **descobertos**, nunca uma string fixa.

### 3. Manifesto por perfil e `extends`
Cada perfil pode declarar `profile.toml` com `extends = "<base>"`. Um overlay com `extends`
é **composto** sobre o base homônimo; sem `extends`, é um perfil **standalone** (comportamento
atual preservado). O `toml_get` atual lê `extends` com segurança (ocorrência única no
arquivo). É **obrigatório** detectar **ciclos** (`A→B→A`) e definir a **ordem de busca** do
base quando houver colisão de nome entre o diretório do framework e o externo.

### 4. Contrato de composição (semântica formal)
A composição reusa a lógica de ilhas e o `jq`, fixando o contrato:

- **Híbrido de texto:** *o base é dono do corpo/regras; o overlay customiza apenas as
  ilhas `USER:*`* (mapeamento `src=base, dst=overlay`). Para **sobrescrever uma regra**
  (corpo), o overlay deve fornecer o arquivo inteiro (balde `rule`) — o modelo de ilha não
  expressa override de corpo.
- **Híbrido JSON (`settings.json`):** deep-merge `jq` com o **overlay vencendo**. ⚠️ Arrays
  (`permissions.deny`/`ask`) são **substituídos por inteiro**, não unidos: customizar `deny`
  no overlay obriga a repetir as entradas herdadas do base.

### 5. Precedência das três camadas
Quando há base + overlay aplicados a um alvo já instalado (`--update`), a regra é
**`base < overlay < edições-no-alvo`**. Consequência explícita: **editar uma ilha no
overlay não retroage** a um alvo já instalado, pois o `--update` faz a ilha do *alvo*
vencer. Isso deve ser comunicado ao usuário na saída do comando.

### 6. Scaffolding
Nova flag (ex.: `--new-profile <nome> [--extends <base>]`) que cria o esqueleto de um
overlay no diretório externo (manifesto `profile.toml` + `AGENTS.md` só com as ilhas
`USER:*`), para o usuário começar do contrato correto sem copiar à mão.

## Consequências

- **Impacto positivo:** usuários criam e versionam perfis próprios sem tocar no repo do
  framework; edições sobrevivem ao `git pull`; os três padrões viram *base* reutilizável.
- **Impacto positivo:** reuso do motor de merge já testado — sem segundo mecanismo de
  composição para manter.
- **Impacto negativo / trade-off aceito:** o modelo de ilha é **assimétrico** (overlay só
  customiza ilhas, não regras de corpo); precedência de três camadas é sutil e exige
  comunicação clara, sob pena de o usuário achar que uma edição no overlay propagou quando
  não propagou.
- **Impacto negativo:** exige um **refactor** do script (separar "computar merge" de
  "política/`--dry-run`") para materializar o "efetivo" da composição — ver Diretriz.

## Diretriz de Conformidade de Código

- **Obrigatório:** antes de promover a `Accepted`, **refatorar** `setup-profile.sh`
  extraindo núcleos puros `merge_text(base,overlay)->path` e `merge_json(base,overlay)->path`,
  deixando `--dry-run` e mensageria **apenas** na camada de instalação. Hoje
  `update_text_hybrid` (`:234`) e `update_json_settings` (`:250`) **não materializam** o
  arquivo sob `--dry-run`, o que inviabiliza a composição em dois estágios.
- **Obrigatório:** parametrizar a mensageria de **órfãos** (`:221`/`:225`): em composição,
  uma ilha presente no overlay e ausente no base é uma **adição**, não "seção removida do
  framework".
- **Obrigatório:** detectar ciclos de `extends` e falhar com mensagem clara; definir e
  documentar a ordem de busca do base.
- **Obrigatório:** adicionar `trap` de limpeza dos `mktemp`/`mktemp -d` sob `set -e` ao
  introduzir o estágio de composição (hoje a limpeza está só no fim, `:242`).
- **Proibido:** manter qualquer lista hardcoded de perfis em validação, ajuda ou mensagens
  de erro após esta mudança.
- **Proibido:** alterar a semântica do `--update` existente (edições-no-alvo continuam
  vencendo) — a composição é uma camada *anterior*, não um substituto.

> Qualquer desvio desta regra viola as diretrizes de conformidade arquitetural do projeto
> e deve ser reportado para revisão antes de prosseguir.

## Referências

- Motor de merge atual: `scripts/setup-profile.sh:133-270`
- Geração de adaptador de skills: `scripts/setup-profile.sh:384-407`
- ADR relacionado: [0005](0005-config-de-servicos-e-skills-overlay.md) (skills overlay do projeto)
