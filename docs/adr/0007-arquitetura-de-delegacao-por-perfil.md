<!-- Caminho relativo: docs/adr/0007-arquitetura-de-delegacao-por-perfil.md -->

# ADR 0007: Arquitetura de delegação (nuvem planeja, local lê) distribuída por perfil

- **Status:** Accepted
- **Data:** 2026-07-28
- **Decisores:** Iago Leal (mantenedor)
- **Tags:** interop, agentry, perfis, confidencialidade, delegação

## Contexto

A ADR-0006 estabeleceu que este repositório distribui `.agentry/agentry.settings.json` por
perfil — **valores**, nunca schema (que pertence ao `agentry`, ADR-0018 daquele repo). Os três
arquivos existem desde então, cobrindo `permissions.deny`/`ask` e as flags de contexto.

Desde então o `agentry` ganhou três capacidades que mudam o que um perfil consegue expressar:

- **ADR-0041** (`agentry`): `permissions.readAllow` — escopo de leitura **por caminho**, e
  `subagentPermissions` — conjunto próprio de permissões para o subagente. Juntos, permitem
  que um agente seja *estruturalmente incapaz* de abrir um arquivo enquanto o subagente,
  rodando num modelo local, continua podendo.
- **ADR-0042** (`agentry`): provider `claude-cli` com ponte MCP — a assinatura Claude Pro/Max
  como agente principal, com tool-calling, sob as permissões acima.
- **Emenda à ADR-0012** (`agentry`, 2026-07-24): `providers.ollama.structuredOutput` teve o
  *default* invertido para `false`; o valor `true` que estes arquivos distribuem **quebra o
  tool-calling** em qualquer modelo com suporte nativo.

O mantenedor pediu que a escolha de perfil, sozinha, decidisse a postura de delegação: um
repositório sob `empresa` mantém tudo local; um sob `pessoal` usa a nuvem para planejar e
delega ao modelo local o que toca dado sensível — **sem editar arquivo de configuração a cada
projeto**.

## Decisão

Os três arquivos por perfil passam a distribuir a arquitetura de delegação completa, com
valores diferenciados. Continua valendo a divisão da ADR-0006: aqui só há **valores**.

### 1. `profile` passa a ser declarado no próprio arquivo

Hoje nenhum dos três declara `profile`, e o `agentry` deriva a classe de egresso justamente
desse campo — logo `--init --profile pessoal` produzia um arquivo que **não** liberava nuvem.
Corrigido: cada arquivo declara o seu próprio perfil. É o campo que faz a escolha de perfil ter
efeito sozinha, que é todo o objetivo desta ADR.

### 2. `chat` com dois candidatos, em ordem

Todos os perfis declaram a mesma `chat`: `claude-cli` (`cloud-ok`) seguido de `ollama`
(`local-only`). **A mesma declaração serve aos três** porque o `agentry` filtra candidatos pela
classe de egresso da sessão:

| Perfil | Classe | Candidato escolhido |
|---|---|---|
| `pessoal` | `cloud-ok` | `claude-cli` (nuvem) |
| `externo-confidencial` | `cloud-opt-out` | `ollama` — `claude-cli` exige `cloud-ok` |
| `empresa` | `local-only` | `ollama` |

Nenhuma lógica condicional, nenhuma duplicação: a exclusão da nuvem em `empresa` vem da
**taxonomia de egresso**, não de uma lista que alguém precisa lembrar de manter.

### 3. `readAllow` + `subagentPermissions` em todos os perfis

Mesmo onde a nuvem já está excluída pela classe de egresso. Razão: defesa em profundidade e
consistência de hábito — se alguém afrouxar o perfil de um projeto, a contenção já está no
lugar, em vez de precisar ser lembrada no pior momento. O conteúdo do `readAllow` é
deliberadamente conservador (documentação e manifestos), e `deny` inclui as ferramentas que
`readAllow` **não** alcança (`shell_exec`, `shell_background`, `glob`, `fs_search`) — omiti-las
tornaria o `readAllow` uma falsa sensação de proteção (diretriz de conformidade da ADR-0041 do
`agentry`).

### 4. `structuredOutput` corrigido para `false`

Acompanha a emenda à ADR-0012 do `agentry`. Distribuir `true` hoje entrega um perfil em que
nenhuma ferramenta executa.

### 5. Skill `delegacao-a-subagentes`

Nova skill de governança nesta biblioteca, aplicável aos três perfis: como escrever o pedido
de delegação, o que delegar e o que não, e — explicitamente — **o que a ferramenta não
garante** (a sanitização depende do modelo local obedecer; filtro literal não protege PII).
Fixa **critérios** de escolha de modelo em vez de nomes, com as observações de campo isoladas
num bloco datado e marcado como perecível.

## Consequências

- **Impacto positivo:** trocar de perfil passa a trocar a postura inteira de roteamento e
  contenção; o caso "empresa fechada / pessoal aberto" deixa de exigir edição manual por
  projeto. A correção de `structuredOutput` conserta perfis que hoje entregam tool-calling
  quebrado.
- **Impacto negativo:** os arquivos ficam bem maiores e passam a mencionar providers concretos
  (`claude-cli`, `ollama`), aumentando o acoplamento a decisões do lado executor — mitigado por
  serem só valores de um schema que já é dele.
- **Dependência de ambiente:** `claude-cli` exige o Claude Code instalado e autenticado. O
  `agentry` não registra o provider quando o binário está ausente (ADR-0042), então a rota cai
  no Ollama sozinha — o perfil não quebra em máquina sem Claude Code.
- **Trade-off aceito:** distribuir uma arquitetura opinativa em vez de um mínimo neutro, em
  troca de o perfil ser útil sem edição. Quem discordar sobrescreve no arquivo do projeto, que
  tem precedência.

## Diretriz de Conformidade

- **Proibido:** distribuir `readAllow` sem `shell_exec`/`shell_background`/`glob`/`fs_search`
  em `deny` (falsa proteção); declarar `claude-cli` como candidato **único** de `chat` em
  qualquer perfil (quebraria em máquina sem Claude Code, e em perfil sem nuvem); voltar a
  distribuir `structuredOutput: true`.
- **Obrigatório:** todo arquivo por perfil declara `profile`; a diferenciação entre perfis
  acontece por **classe de egresso**, não por listas de candidatos divergentes; mudança de
  schema continua sendo do `agentry` — uma necessidade nova aqui vira pedido no
  `exchange-log`, nunca um campo inventado neste repositório.
