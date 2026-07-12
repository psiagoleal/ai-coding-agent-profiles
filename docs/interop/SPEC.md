<!-- Caminho relativo: docs/interop/SPEC.md -->

# Contrato de Interoperabilidade — `ai-coding-agent-profiles` ⇄ `agentry`

- **Versão do contrato:** `1` (seções marcadas *(rascunho)* serão ratificadas por ADR no repo dono antes de congelar).
- **Status:** ativo.
- **Fonte canônica:** este arquivo, no repo `ai-coding-agent-profiles`. O repo `agentry` mantém apenas um **ponteiro** em `docs/interop/README.md`, fixando a versão suportada.
- **Última atualização:** 2026-07-12.

> Qualquer agente de IA que trabalhe em **qualquer** dos dois repositórios deve ler este
> documento antes de alterar a fronteira entre eles. Ele define (1) a divisão de
> responsabilidades e (2) o contrato de artefatos que um projeto produz e o outro consome.

## 1. Charter — divisão de responsabilidades

| Dimensão | `ai-coding-agent-profiles` — **POLÍTICA** | `agentry` — **EXECUÇÃO** |
|---|---|---|
| Papel | Define regras, perfis e o *esquema* dos artefatos | Lê os artefatos e **impõe/executa** |
| Possui | `AGENTS.md`, `settings.json`, `.claudeignore`, biblioteca de skills, taxonomia de privacidade | Provider layer, router/egresso, agent loop, tools, MCP, context manager |
| Decide | *Qual* a política (o quê é permitido, por perfil) | *Como* executar a política de forma confiável e auditável |
| **Não faz** | Não executa LLM nem controla rede | Não inventa política; não decide regras por conta própria |

**Princípios:**
1. `profiles` define política; **não executa**. `agentry` executa e impõe; **não inventa política**.
2. Mudança que cruze a fronteira → **ADR** no repo dono **+** entrada no `exchange-log`.
3. Em divergência de versão de contrato, `agentry` **falha fechado** (*fail-closed*) — confidencialidade nunca é degradada silenciosamente.

## 2. Contrato de artefatos (`profiles` → `agentry`)

| Artefato | Esquema | O que `agentry` consome | Estabilidade |
|---|---|---|---|
| `AGENTS.md` | `agents-md:1` | Instruções/regras em Markdown (fonte da verdade do projeto-alvo) | estável |
| `.claude/settings.json` | `settings-schema:1` | Parâmetros de modelo e permissões (`deny`/`ask`) | *(rascunho — ADR-0003 @ `agentry`)* |
| `.agentry/agentry.settings.json` | `agentry-settings-schema:1` | Permissões por nome de tool + flags de contexto (repo-map/RAG/LSP)/provider — schema de propriedade do `agentry` (ADR-0018 @ `agentry`); este repo só distribui *defaults* por perfil (ADR-0006) | *(rascunho — ADR-0018 @ `agentry`)* |
| `SKILL.md` (frontmatter) | `skill-frontmatter:1` | `name`, `description` (gatilho), `allowed-tools`, `model` | estável |
| `.claudeignore` | `claudeignore:1` | Filtros de contexto | estável |
| Taxonomia de privacidade | `privacy-taxonomy:1` | Mapa perfil → classe de egresso (§2.1) | **ratificado** (ADR-0002 @ `agentry`) |

### 2.1 Taxonomia de privacidade *(ratificada por ADR-0002 @ `agentry`)*

| Perfil (`profiles`) | Classe de egresso (`agentry`) | Regra de rede |
|---|---|---|
| `empresa` | `local-only` | Egresso para nuvem **proibido** por padrão; só endpoints on-premise/aprovados na allowlist |
| `externo-confidencial` | `cloud-opt-out` | Nuvem só com opt-out de retenção comprovado; allowlist obrigatória |
| `pessoal` | `cloud-ok` | APIs de nuvem livres (bom senso de custo) |

## 3. Protocolo de troca (`exchange-log`)

- **Log append-only canônico:** `agentry/docs/interop/exchange-log.md` (o lado executor registra as trocas; `profiles` consulta e responde ali).
- Cada troca é uma **entrada datada**: contexto, pedido/decisão, repo de origem, status.
- **Nunca reescrever** entradas — só anexar. Decisões vinculantes viram **ADR** no repo dono; referenciar o ADR na entrada.

## 4. Versionamento

- A versão deste contrato é um **inteiro único**. Mudança incompatível ⇒ `+1` e nota de migração.
- `agentry` declara a versão que suporta. Se o SPEC consumido divergir, **aborta com mensagem explícita** (regra §1.3).

## 5. Descoberta por agentes

- `agentry/AGENTS.md` → seção *Interoperabilidade* aponta para este contrato.
- `ai-coding-agent-profiles/README.md` → seção *Interoperabilidade* aponta para esta pasta.
