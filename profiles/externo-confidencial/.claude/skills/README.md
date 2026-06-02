<!-- Caminho relativo: .claude/skills/README.md -->

# Adaptador de skills do Claude Code

Esta pasta é apenas um **adaptador de descoberta** para o Claude Code. A **fonte da verdade
é independente de agente**: vive na pasta neutra `skills/` na raiz do repositório. Aqui
ficam apenas **ponteiros (symlinks)** para lá — sem duplicar conteúdo.

Forma recomendada (script do framework):

```bash
scripts/setup-profile.sh externo-confidencial <repo-alvo>
scripts/setup-profile.sh externo-confidencial <repo-alvo> --skills-mode copy   # Windows
```

Manualmente:

```bash
ln -s ../../skills/secrets-guard        .claude/skills/secrets-guard
ln -s ../../skills/adr-writer           .claude/skills/adr-writer
ln -s ../../skills/micro-ticket-planner .claude/skills/micro-ticket-planner
ln -s ../../skills/handoff-updater      .claude/skills/handoff-updater
ln -s ../../skills/pr-review-guard      .claude/skills/pr-review-guard
```

No perfil **EXTERNO-CONFIDENCIAL**, todas as cinco são recomendadas — `secrets-guard` é
especialmente crítica dada a cobertura por NDA. Ver `AGENTS.md` seção 9.
