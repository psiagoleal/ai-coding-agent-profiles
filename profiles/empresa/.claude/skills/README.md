<!-- Caminho relativo: .claude/skills/README.md -->

# Adaptador de skills do Claude Code

Esta pasta é apenas um **adaptador de descoberta** para o Claude Code. A **fonte da verdade
é independente de agente**: vive na pasta neutra `skills/` na raiz do repositório. Aqui
ficam apenas **ponteiros (symlinks)** para lá — sem duplicar conteúdo.

A forma recomendada de popular ambos é o script do framework:

```bash
scripts/setup-profile.sh empresa <repo-alvo>            # symlinks (padrão)
scripts/setup-profile.sh empresa <repo-alvo> --skills-mode copy   # cópias (Windows)
```

Manualmente:

```bash
ln -s ../../skills/secrets-guard        .claude/skills/secrets-guard
ln -s ../../skills/adr-writer           .claude/skills/adr-writer
ln -s ../../skills/micro-ticket-planner .claude/skills/micro-ticket-planner
ln -s ../../skills/handoff-updater      .claude/skills/handoff-updater
ln -s ../../skills/pr-review-guard      .claude/skills/pr-review-guard
```

No perfil **EMPRESA**, todas as cinco skills de governança são recomendadas.
Ver `AGENTS.md` seção 9 para quando acionar cada uma.
