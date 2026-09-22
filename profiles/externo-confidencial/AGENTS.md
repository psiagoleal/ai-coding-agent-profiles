<!-- Caminho relativo: AGENTS.md -->

# AGENTS.md — Perfil EXTERNO-CONFIDENCIAL (projetos de cliente sob NDA)

> **Fonte única da verdade** para qualquer agente de IA neste repositório. Leitura
> compulsória antes de editar. `CLAUDE.md`, `.cursorrules` e
> `.github/copilot-instructions.md` apenas apontam para este documento.

## Início — por onde começar

> Para o agente e para o humano. Vale quando o projeto ainda não tem `docs/architecture.md`
> e `docs/TICKETS.md`, ou quando alguém pergunta "por onde começo".

- **Projeto novo:** entrevista sobre o objetivo → spec pequena (`spec-como-contrato`) → ADR
  de stack (`adr-writer`) → tickets em `docs/TICKETS.md` (`micro-ticket-planner`) → teste
  falhando antes do código (`teste-primeiro`) → revisão antes do merge (`pr-review-guard`).
- **Projeto existente entrando agora no processo:** **levantar antes de mudar** — segredos
  já versionados (`secrets-guard`), comandos reais de build e teste, `docs/architecture.md`
  gerado do código (`mapa-de-arquitetura`), `docs/CURRENT-STATE.md` com o estado real
  (`handoff-updater`). Só então tickets e código, com teste de caracterização onde não há
  teste.
- **Nos dois:** o humano escolhe o perfil e aprova spec, ADR e merge; o agente prepara.
  Roteiro completo, com quem decide cada passo: skill `novo-projeto`, seção 7.

## 0. Perfil e postura de confidencialidade

- **Perfil:** projetos particulares para clientes, fora da empresa, **com confidencialidade
  contratual (NDA)**. Sem a infraestrutura corporativa — o desenvolvedor é responsável
  pela governança.
- **Confidencialidade:** **ALTA**. Todo dado, código e regra de negócio do cliente é
  sensível e coberto por NDA. Não compartilhar, não publicar, não reutilizar em outros
  projetos.
- **Modelos permitidos:** APIs comerciais são aceitáveis **desde que** configurado o
  **opt-out de retenção/treino de dados** no provedor. Nunca colar dados do cliente em
  contas gratuitas/pessoais sem garantia de não-retenção. Prefira projetos com *zero data
  retention* quando disponível.

<!-- USER:BEGIN id=confidencialidade-projeto -->
_(nenhuma — acrescente aqui restrições de confidencialidade próprias deste repositório,
ex.: fronteira com projetos sob NDA, origem permitida de fixtures, o que nunca pode ser
publicado.)_
<!-- USER:END -->

## 1. Ambiente de desenvolvimento

<!-- USER:BEGIN id=ambiente-desenvolvimento -->
- SO: **Ubuntu 26** · Shell: **zsh**
- Python: **uv** · Versão: **git** · IDE: **Zed IDE** · Containerização: **Docker**
<!-- USER:END -->

## 2. Comandos exatos (ajuste por projeto)

<!-- USER:BEGIN id=comandos-exatos -->
```bash
uv sync
ruff check . --fix --select E,W,F
black . && isort .
mypy src/ --ignore-missing-imports
pytest -v --cov=src
```
<!-- USER:END -->

> Mantenha esta seção fiel ao projeto do cliente. O agente não deve adivinhar comandos.

## 3. Estrutura de diretórios e mapeamento

<!-- USER:BEGIN id=estrutura-diretorios -->
```
src/                 # código-fonte do projeto do cliente
tests/               # testes
docs/adr/            # ADRs — leitura obrigatória
docs/CURRENT-STATE.md# handoff entre turnos
data/                # dados do cliente — SENSÍVEIS, ver .claudeignore
```
<!-- USER:END -->

## 4. Estilo de codificação

<!-- USER:BEGIN id=estilo-codificacao -->
Idêntico ao padrão pessoal do desenvolvedor:

- Comentário de **caminho relativo** no topo de cada arquivo.
- **Doxygen** (C++), **Type Hints** (Python).
- Formatadores: `clang-format`, `black`+`isort`, `rustfmt`, `prettier`.
- Sem mascarar erros com `except`/`catch` vazio.
- Documentação Markdown com Mermaid e LaTeX.
- Evitar viés de confirmação; propor alternativas; basear-se em documentação oficial e
  apresentar mudanças como *diff* estilo git.
<!-- USER:END -->

## 5. Economia de tokens e higiene de sessão

- Comunicação sintética, sem saudações; sessão ociosa evitada.
- Poda/reinício de sessão ao primeiro sinal de degradação.
- Fluxo híbrido por tarefa (fronteira p/ arquitetura, autocompletação p/ implementação,
  subagentes econômicos p/ varredura).
- Parametrização em `.claude/settings.json`; filtros em `.claudeignore`.

## 6. Fronteiras e restrições de modificação

- **Proibido** expor credenciais ou alterar `.env`.
- **Não** criar/reescrever migrações SQL manualmente sem aprovação.
- Dependências (`pyproject.toml`/`requirements.txt`) só mudam **sob aprovação explícita**.
- Respeitar integralmente as cláusulas do NDA quanto a bibliotecas/serviços permitidos.

<!-- USER:BEGIN id=adendos-fronteiras -->
_(nenhum — acrescente aqui restrições de modificação próprias deste projeto.)_
<!-- USER:END -->

## 7. Segurança e segredos (OBRIGATÓRIO)

Os quatro princípios de não-exposição (ver skill `secrets-guard`) valem integralmente:

1. **Nunca** executar comandos que exibam segredos.
2. **Avaliar antes** se a saída pode conter material sensível; na dúvida, abster-se.
3. Preferir **verificações indiretas**.
4. Inspeção inevitável → **delegar ao operador humano**.

- **Cofre (equipe pequena):** Doppler, Infisical ou 1Password Secrets Automation, com
  restrição por ambiente. Injeção de credenciais apenas em tempo de execução.
- **Dados do cliente:** tratados como sensíveis sob NDA — nunca em prompts de contas sem
  opt-out de retenção, nunca em repositórios públicos.
- **Sandbox recomendada/obrigatória:** contêineres efêmeros / *worktrees*; evitar
  `--dangerously-skip-permissions` em qualquer base que toque dados do cliente.
- **Injeção indireta:** *allowlist* de domínios; separar canais instrucionais de canais de
  dados; revisar *diffs* com atenção a arquivos sensíveis.
- **Proveniência:** varredura de segredos pré-commit (`gitleaks`). Quando o contrato
  exigir rastreabilidade do uso de IA, registrá-lo **apenas na mensagem de commit**, ao
  final, **entre chaves**: `{agente: <nome>; modelo: <modelo/versão>}`. **Nenhum outro
  artefato** (código, ADR, handoff, descrição/metadado de PR) deve mencionar uso de IA nem
  atribuir autoria, coautoria ou decisão a um agente.

<!-- USER:BEGIN id=adendos-seguranca -->
_(nenhum — acrescente aqui o cofre, caminhos de credencial e regras de segredo deste projeto.)_
<!-- USER:END -->

## 8. Fluxo ágil

  **Nenhuma outra entrada** em commit ou documentação: sem link ou ID de sessão de agente,
  sem URL de conversa, sem rodapé do tipo "Generated with…", sem *trailers*
  (`Co-authored-by`, `Assisted-by`, `Generated-by`, `*-Session`). O marcador entre chaves é o
  único registro permitido — mesmo que a ferramenta ofereça outro por padrão.
  Controle estrutural: hook `commit-msg` da skill `pr-review-guard`.
- **Contrato antes do código:** trabalho de risco começa por spec com critério de aceite
  verificável (skill `spec-como-contrato`); trabalho leve, pelo critério de aceite direto.
- **Teste antes da implementação:** comportamento novo e correção de bug começam por um
  teste que falha pelo motivo certo, com a saída citada (skill `teste-primeiro`).
- **Painel de tickets** em `docs/TICKETS.md`, **sempre atualizado** ao criar, concluir ou
  abandonar um ticket: uma linha por ticket, com link para o detalhe (skill
  `micro-ticket-planner`).
- **Mapa de arquitetura** em `docs/architecture.md`: a arquitetura **efetiva**, derivada das
  dependências reais entre módulos, sem encaixe forçado em padrão; atualizado no mesmo
  trabalho que mudar módulos ou dependências (skill `mapa-de-arquitetura`).
- **Micro-tickets** (skill `micro-ticket-planner`).
- **Handoff** em `docs/CURRENT-STATE.md` a cada commit (skill `handoff-updater`).
- **DoD:** testes/linter/tipagem passam; revisão de PR (skill `pr-review-guard`)
  **validada por humano** antes do merge.
- **ADRs** obrigatórios antes de mudanças funcionais (skill `adr-writer`).

<!-- USER:BEGIN id=adendos-fluxo -->
_(nenhum — acrescente aqui adaptações de DoD, convenção de commit e ritos deste projeto.)_
<!-- USER:END -->

## 9. Skills disponíveis

- **`secrets-guard`**, **`adr-writer`**, **`micro-ticket-planner`**, **`handoff-updater`**,
  **`pr-review-guard`**, **`delegacao-a-subagentes`**, **`delegacao-openai-compat`**,
  **`meeting-minutes`**,
  **`novo-projeto`**, **`limites-de-uso`**, **`caveman`**,
  **`atribuicao-de-falha`**, **`gates-de-conclusao`**, **`paralelizacao-em-grafo`**, **`spec-como-contrato`**,
  **`teste-primeiro`**, **`critico-independente`**, **`mapa-de-arquitetura`** — todas recomendadas. Ver seção 9 do perfil empresa para os gatilhos
  de cada uma, e [`skills/README.md`](./skills/README.md) para o catálogo completo
  (incluindo as skills de domínio, instaladas só sob demanda).

<!-- USER:BEGIN id=adendos-skills -->
_(nenhum — acrescente aqui skills próprias deste projeto e ressalvas de uso.)_
<!-- USER:END -->

## 10. Seções específicas do projeto

> Espaço reservado ao projeto. O conteúdo **dentro** do marcador abaixo é preservado por
> `setup-profile.sh --update`; o que está fora dele é regramento do framework e será
> regenerado. Acrescente aqui as seções que só fazem sentido neste repositório — modo de
> pesquisa, contratos de interoperabilidade, particularidades de domínio.
>
> Para criar um ponto de customização em outra seção, abra um par de marcadores próprio
> no mesmo formato dos usados neste arquivo, com um id só seu. Ids que o framework não
> conhece são preservados na atualização e reagrupados ao final do arquivo para revisão.

<!-- USER:BEGIN id=secoes-adicionais -->
_(nenhuma — remova esta linha ao acrescentar a primeira seção)_
<!-- USER:END -->
