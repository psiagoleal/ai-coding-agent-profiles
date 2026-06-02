<!-- Caminho relativo: AGENTS.md -->

# AGENTS.md — Perfil EXTERNO-CONFIDENCIAL (projetos de cliente sob NDA)

> **Fonte única da verdade** para qualquer agente de IA neste repositório. Leitura
> compulsória antes de editar. `CLAUDE.md`, `.cursorrules` e
> `.github/copilot-instructions.md` apenas apontam para este documento.

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

## 1. Ambiente de desenvolvimento

- SO: **WSL2 com Ubuntu 24** · Shell: **zsh**
- Python: **uv** · Versão: **git** · IDE: **VSCode** · Containerização: **Docker**

## 2. Comandos exatos (ajuste por projeto)

```bash
uv sync
ruff check . --fix --select E,W,F
black . && isort .
mypy src/ --ignore-missing-imports
pytest -v --cov=src
```

> Mantenha esta seção fiel ao projeto do cliente. O agente não deve adivinhar comandos.

## 3. Estrutura de diretórios e mapeamento

```
src/                 # código-fonte do projeto do cliente
tests/               # testes
docs/adr/            # ADRs — leitura obrigatória
docs/CURRENT-STATE.md# handoff entre turnos
data/                # dados do cliente — SENSÍVEIS, ver .claudeignore
```

## 4. Estilo de codificação

Idêntico ao padrão pessoal do desenvolvedor:

- Comentário de **caminho relativo** no topo de cada arquivo.
- **Doxygen** (C++), **Type Hints** (Python).
- Formatadores: `clang-format`, `black`+`isort`, `rustfmt`, `prettier`.
- Sem mascarar erros com `except`/`catch` vazio.
- Documentação Markdown com Mermaid e LaTeX.
- Evitar viés de confirmação; propor alternativas; basear-se em documentação oficial e
  apresentar mudanças como *diff* estilo git.

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
- **Proveniência:** varredura de segredos pré-commit (`gitleaks`); registrar
  modelo/versão/prompt em *trailers* quando o contrato exigir rastreabilidade.

## 8. Fluxo ágil

- **Micro-tickets** (skill `micro-ticket-planner`).
- **Handoff** em `docs/CURRENT-STATE.md` a cada commit (skill `handoff-updater`).
- **DoD:** testes/linter/tipagem passam; revisão de PR (skill `pr-review-guard`)
  **validada por humano** antes do merge.
- **ADRs** obrigatórios antes de mudanças funcionais (skill `adr-writer`).

## 9. Skills disponíveis

- **`secrets-guard`**, **`adr-writer`**, **`micro-ticket-planner`**,
  **`handoff-updater`**, **`pr-review-guard`** — todas recomendadas. Ver seção 9 do perfil
  empresa para os gatilhos de cada uma.
