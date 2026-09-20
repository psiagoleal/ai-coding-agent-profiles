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

1. **Quatro skills novas**, fechando a lacuna de SDD/TDD que a varredura confirmou (nenhum
   perfil mencionava nenhum dos dois): `spec-como-contrato`, `teste-primeiro`,
   `critico-independente` e `dominio/transcrever-video`. A seção 8 dos três perfis passa a
   exigir contrato antes do código e teste antes da implementação, proporcionais ao risco.
2. **22 repositórios de `~/dev` atualizados** — agora **com** linha de base: o aviso de
   "sem linha de base" sumiu e o `--update` passou a poder distinguir template de edição local.
   Zero conflitos. Públicos (`agentry`, `atldp`, `docling_service`, `neocad`) seguem só com a
   biblioteca pública, conferido com o verificador de vazamento em cada um.
3. **Dois `.claudeignore` legados migrados** (`btc_market`, `neocad`): os padrões próprios do
   projeto passaram para dentro de uma ilha `USER`, então sobrevivem às próximas atualizações.
   Conferido pelo git que nenhuma linha se perdeu; atualização seguinte roda sem conflito.
4. Transcrição do vídeo de referência obtida **sem Whisper e sem ffmpeg**, pela legenda da
   própria plataforma — caminho que virou a skill `dominio/transcrever-video`.

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

- **Sem VPN**, o gateway OpenAI-compatible fica inalcançável: as rotas `oa-chat` e `agentry
  --task-class delegada` não funcionam até o acesso voltar. A configuração está pronta e
  validada (`local-only`, `baseUrl` com `/v1`); falta só conectividade.
- A variável `AGENTRY_LITELLM_BASE_URL` no `~/.zshrc` (linha 207) **não** termina em `/v1`, e
  vence o arquivo global. Precisa da correção do mantenedor, senão o `agentry` monta a URL
  errada mesmo com a VPN de volta.

## Próximo passo

1. **Com a VPN de volta:** exercitar a `critico-independente` de ponta a ponta — submeter um
   trabalho recente ao GLM como crítico e ver se ele acrescenta sinal ou só concorda.
2. Exercitar os adaptadores de subagent ao vivo (`codex debug prompt-input`,
   `opencode agent list`) — hoje a prova é de gramática e parsing, não de carga real.
3. Gerador de subagents para Gemini e Copilot.
4. Reclassificar as skills de domínio antigas com migração para instalações existentes.

## Ação pendente fora deste repositório

`agentry` (solicitado à sessão do projeto em 2026-09-17): descobrir skills em `.agents/skills/`
além de `.claude/skills/`, por precedência sem merge (ADRs 0020/0023 dele). Roadmap, só
informado: subagent por papel nomeado, além do despacho por `task_class`.

> Rodadas encerradas e tabela de commits: [`docs/handoff-arquivo.md`](handoff-arquivo.md).
