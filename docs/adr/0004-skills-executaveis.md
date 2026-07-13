<!-- Caminho relativo: docs/adr/0004-skills-executaveis.md -->

# ADR 0004: Skills executáveis com scripts anexos (declarativo → executável)

- **Status:** Proposed <!-- pendente de validação de implementação antes de Accepted -->
- **Data:** 2026-06-19
- **Decisores:** Equipe técnica
- **Tags:** skills, execução, segurança, permissões, secrets-guard

## Contexto

As skills do framework são hoje **100% declarativas**: cada uma é só um `SKILL.md`
(governança/fluxo), e `skills/README.md` posiciona a execução como responsabilidade de
servidores **MCP** (`skills/README.md:83-96`), embora já mencione "skills com scripts
anexos" (`:80`).

Surgiu a necessidade de skills que **executem ferramentas locais** — o caso motivador é
**busca via searxng** (um serviço HTTP self-hosted) com URL configurável. Decidiu-se (com o
usuário) que essas skills carregam um **script anexo** que faz a chamada, em vez de exigir
um servidor MCP dedicado — modelo mais leve e suficiente para integrações locais simples.

Isso **muda o modelo de ameaça** do framework: introduz código executável rodando com os
privilégios do shell do agente, dentro de skills que (pelo ADR 0005) podem ser *overlay do
projeto*, isto é, de proveniência menos controlada que a biblioteca do framework.

## Decisão

> **Proposta (não ratificada).** Fica proposto permitir **skills executáveis** via scripts
> anexos, com um contrato de runtime baseado em variável de ambiente e uma postura de
> segurança explícita, condicionado à validação descrita na Diretriz de Conformidade.

### 1. Estrutura e transporte
A skill traz uma subpasta `scripts/` (ex.: `skills/web-search/scripts/search.sh`). Os loops
`find -type f` (`setup-profile.sh:374-377`) e `cp -r` (`:403`) **já transportam** essa
subpasta — não é preciso mudar a cópia.

### 2. Invocação por interpretador
Os scripts são **sempre** invocados via interpretador (`bash search.sh`, `python
search.py`), **nunca** `./search.sh`. O bit de execução não sobrevive a checkouts no Windows
nem ao modo `--skills-mode copy`/`symlink` de forma confiável.

### 3. Contrato de runtime via variável de ambiente
O endpoint do serviço é lido de **env var** (ex.: `SEARXNG_URL`), nunca embutido no script.
O script **valida defensivamente** antes de qualquer chamada de rede: a variável deve estar
**não-vazia** e **não conter** o literal de placeholder (`{{`). Em falha, aborta com
mensagem clara — **nunca** dispara HTTP para placeholder ou string vazia. (A semeadura da
env var a partir do `config.toml` é tratada no ADR 0005.)

### 4. Skill de referência
Cria-se `skills/web-search/` (`SKILL.md` + `scripts/search.sh`) como exemplo canônico do
padrão searxng, servindo de molde para skills executáveis futuras e para overlays do usuário.

## Consequências

- **Impacto positivo:** skills passam a integrar ferramentas locais (busca, lint, geradores)
  sem o peso de um servidor MCP, mantendo a portabilidade do `SKILL.md`.
- **Impacto positivo:** o contrato por env var mantém endpoints fora do código versionado e
  configuráveis por ambiente.
- **Impacto negativo (segurança):** introduz **execução de código** no fluxo do agente — ver
  riscos e mitigações na Diretriz. Esta é a consequência dominante deste ADR.
- **Trade-off aceito:** abrir mão do isolamento/observabilidade que um MCP daria, em troca de
  leveza, **compensado** por gates de permissão e validação defensiva.

## Diretriz de Conformidade de Código

- **Crítico — ponto cego da deny-list:** um script (sobretudo Python) lê `os.environ` e pode
  exfiltrar segredos **sem disparar** `Bash(env)`/`Bash(printenv*)`. Autorizar
  `Bash(python .../search.py)` **contorna** a deny-list de segredos da skill `secrets-guard`.
  **Obrigatório:** a execução de scripts de skill deve passar por **`ask`-gate** (não
  `allow` silencioso) nos perfis e, quando viável, o ambiente passado ao script deve conter
  **apenas** a env var necessária, não o ambiente completo.
- **Obrigatório (egress):** nos perfis `empresa` e `externo-confidencial`, a URL
  repontável é vetor de **exfiltração** (apontar o serviço para host do atacante). A execução
  de scripts de skill deve ser `ask`/`deny` (ou restrita por allowlist de host) nesses
  perfis; no `pessoal`, postura mais relaxada é aceitável.
- **Obrigatório:** todo script anexo valida o contrato de runtime (env var não-vazia e sem
  `{{`) **antes** de qualquer I/O de rede, falhando de forma limpa.
- **Obrigatório:** scripts de skill **overlay** (proveniência do projeto, ADR 0005) são
  tratados como **código** — revisão por pares obrigatória; nunca executar script de skill
  de origem não revisada.
- **Proibido:** embutir endpoints/credenciais no corpo do script; o único canal é a env var.
- **Proibido:** invocar scripts via `./script` dependente de bit de execução.

> Qualquer desvio desta regra viola as diretrizes de conformidade arquitetural do projeto
> e deve ser reportado para revisão antes de prosseguir.

## Referências

- Posição atual "skills declarativas vs MCP": `skills/README.md:83-96`
- Transporte de subpastas de skill: `scripts/setup-profile.sh:374-377`, `:403`
- ADR relacionado: [0005](0005-config-de-servicos-e-skills-overlay.md) (config da URL e skills overlay)
