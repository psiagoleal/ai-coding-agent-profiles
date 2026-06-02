<!-- Caminho relativo: .claude/skills/README.md -->

# Adaptador de skills do Claude Code

Esta pasta é apenas um **adaptador de descoberta** para o Claude Code. A **fonte da verdade
é independente de agente**: vive na pasta neutra `skills/` na raiz do repositório. Aqui
ficam apenas **ponteiros (symlinks)** para lá — sem duplicar conteúdo.

Forma recomendada (script do framework):

```bash
scripts/setup-profile.sh pessoal <repo-alvo>
# só as skills mais usadas neste perfil:
scripts/setup-profile.sh pessoal <repo-alvo> --skills secrets-guard,pr-review-guard
```

Manualmente:

```bash
ln -s ../../skills/secrets-guard   .claude/skills/secrets-guard
ln -s ../../skills/pr-review-guard .claude/skills/pr-review-guard
# opcionais conforme o projeto: adr-writer, micro-ticket-planner, handoff-updater
```

No perfil **PESSOAL**, `secrets-guard` é sempre recomendada (segredos pessoais em repo
público); as demais conforme a necessidade. Ver `AGENTS.md` seção 9.
