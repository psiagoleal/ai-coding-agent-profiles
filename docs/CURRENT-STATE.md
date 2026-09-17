<!-- Caminho relativo: docs/CURRENT-STATE.md -->

# Estado Corrente (Handoff) — Framework

> Fonte central de sincronização entre turnos. Atualizado a cada commit. Não inclua segredos.
> Mantido conforme a skill `handoff-updater`.

## Último turno

- **Data:** 2026-09-17
- **Branch:** `main`
- **Commit:** `(pendente — nada commitado desde 828c978)`
- **Autor do turno:** Iago Leal (mantenedor), com Claude Code

## Metas cumpridas neste turno

1. **Separação público × privado.** Material não publicável (acervo de terceiros com
   procedência pendente) e de uso pessoal (`pc-builder`, `aula-audio`) saiu deste repositório
   para uma **biblioteca extra privada**, mantida pelo mesmo agente. Nada disso esteve em commit
   aqui — a separação não exigiu reescrever histórico. Menções a esse material foram retiradas
   das ADRs 0011/0012, do catálogo, dos perfis e da `caveman`.
2. **ADR 0013** — taxonomia por categoria (governança na raiz; categorias opt-in), subagents na
   fonte neutra `agents/` em formato Claude Code, **bibliotecas múltiplas** e mapa de
   portabilidade (`docs/interop/portabilidade.md`).
3. **Instalador.** `--fonte <dir>` / `fontes_extras` (config pessoal); colisão de nome entre
   fontes é erro antes de escrever; `--agents auto|all|none|lista` (adaptador só Claude);
   `--skills` com nome sem caminho, `'categoria/*'` e `@padrao`; aviso de dependência entre
   skills. Corrigidos: nome inválido ignorado em silêncio; seleção inválida deixava
   instalação pela metade.
4. **`--update` não perde edição local fora das ilhas** — linha de base em
   `.agent-profile/baseline.sha256`, desvio para `<arq>.new`. Oito cenários exercitados.
5. **`delegacao-openai-compat`** (ex-`delegacao-litellm`) com `oa-chat`: chave e corpo fora de
   argv, `--no-think`, código 3 para resposta vazia/truncada.
6. Regra de *trailers* uniformizada entre `pessoal` e `empresa`. Pedido ao `agentry` enviado
   para descobrir skills em `.agents/skills` (precedência sem merge).
7. **Subagents portáveis para Codex e OpenCode** — `scripts/gerar-agent-adapter.py` gera o
   cabeçalho de cada harness a partir do canônico, mantendo o corpo idêntico; `sandbox_mode`
   e `permission` derivam das tools, e `model` vira **nível** de raciocínio. Ligado ao
   `--agent`. Conferido em 44 subagents: TOML válido em todos, corpo byte a byte igual.
8. **Publicado.** Sete commits temáticos enviados (`828c978..`), todos com o verificador de
   vazamento limpo no índice. Biblioteca privada criada, commitada e enviada a remoto
   **privado** (visibilidade confirmada após o push).

## Em andamento (herdado, inalterado)

- [ ] ADRs 0001–0006 seguem `Proposed`. 0003–0006 só viram `Accepted` após a validação de
      implementação da Diretriz de Conformidade de cada um — para a 0006, isso é o `agentry`
      de fato consumir o arquivo (MT-39/MT-40 daquele repo).
- [ ] 0001 (RTK) e 0002 (OKF) pendentes da reanálise de maturidade (desde 2026-06-19).
- [ ] ADRs 0003–0005 (perfis base+overlay, skills executáveis, config de serviços)
      **não implementados** — depende do refactor central do `setup-profile.sh`
      (separar núcleo de merge da política de instalação/`--dry-run`).

> Rodadas encerradas: [`docs/handoff-arquivo.md`](handoff-arquivo.md).

## Impedimentos abertos

- Nenhum neste repositório. Publicação do acervo de terceiros é tratada na biblioteca privada.

## Próximo passo

1. Exercitar os adaptadores gerados **ao vivo** nas CLIs (`codex debug prompt-input`,
   `opencode agent list`) — hoje a prova é de gramática e parsing, não de carga real.
2. Gerador para Gemini e Copilot — mesmo script, ramo novo.
3. Revisar menções a `CLAUDE.md` e usos de tool de subagent nos corpos (portabilidade).
4. Reclassificar as skills de domínio antigas com migração para instalações existentes.
5. O hook de pre-commit é **local**: reinstalar em cada clone novo deste repositório.

## Ação pendente fora deste repositório

`agentry` (solicitado à sessão do projeto em 2026-09-17): descobrir skills em `.agents/skills/`
além de `.claude/skills/`, por precedência sem merge (ADRs 0020/0023 dele). Roadmap, só
informado: subagent por papel nomeado, além do despacho por `task_class`.

> Rodadas encerradas e tabela de commits: [`docs/handoff-arquivo.md`](handoff-arquivo.md).
