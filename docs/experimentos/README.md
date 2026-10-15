<!-- Caminho relativo: docs/experimentos/README.md -->

# Experimentos

Um diretório por experimento controlado de instrução — prompt de sistema, regra, skill —, no
método da skill [`experimento-controlado`](../../skills/experimento-controlado/SKILL.md).
Experimento decide adoção ou recusa; o resultado vai para o ticket, para a skill que ele
justifica ou para [`docs/recusados/`](../recusados/README.md).

| Experimento | Pergunta | Estado | Resultado |
|---|---|---|---|
| [EXP-0001](EXP-0001-afirmacao-verificavel/README.md) | regras de afirmação verificável reduzem afirmação sem sustentação, sem aumentar ressalva? | rascunho | — |

## Anatomia

```
EXP-NNNN-<slug>/
  README.md          registro: hipótese, critério, braços, casos, piloto, resultado, não medido
  experimento.json   manifesto — o commit dele é o pré-registro
  bracos/            controle.md e tratamento.md (a base é o modelo sem sistema)
  casos/             um pedido por arquivo
  rubricas/          uma por caso corrigido por juiz
  execucoes/         registro bruto de cada execução — fora do git (ver abaixo)
```

Modelos: `skills/experimento-controlado/templates/`.

## Onde rodar: o worktree de experimentos

Experimento roda num **worktree próprio, de caminho fixo**, fora da cópia em que se trabalha:

```
~/dev/ai-coding-agent-profiles-experimentos     branch local `experimentos`
```

Por que ali, e não em `.claude/worktrees/`:

- **É permanente.** Os worktrees de `.claude/worktrees/` são de sessão, e o harness oferece
  removê-los quando a sessão acaba. Experimento atravessa sessões.
- **Não contamina a verificação local.** Enquanto o MT-48 estiver aberto, todo worktree sob
  `.claude/worktrees/` entra na contagem do verificador de links, e a conta local deixa de bater
  com a do CI.
- **Toda sessão sabe onde está.** Caminho fixo dispensa perguntar.

Três regras mantêm o worktree barato:

1. **Ele só escreve sob `docs/experimentos/`.** Assim o merge em `main` nunca conflita com o
   trabalho de outras frentes. O tratamento mora dentro do experimento até passar; a skill que
   ele justificar nasce depois, no fluxo normal.
2. **A branch `experimentos` não vai ao remoto.** O que precisa sobreviver é o registro, e ele
   chega pelo merge em `main`.
3. **O registro bruto não vai ao git.** `execucoes/` está no `.gitignore`: as respostas são
   volumosas, e um experimento futuro pode usar caso tirado de material que não é público. O que
   se versiona é o resumo colado no `README.md` do experimento. Se a resposta bruta for a prova
   de uma decisão, ela vai para o repositório privado, no mesmo caminho.

Experimento com caso tirado de projeto confidencial mora inteiro no repositório privado, com a
mesma anatomia. Nunca aqui.

### Comandos

Pelo combinado de git deste repositório, o agente propõe e a pessoa executa.

```bash
# uma vez: criar o worktree
git -C ~/dev/ai-coding-agent-profiles worktree add -b experimentos \
    ~/dev/ai-coding-agent-profiles-experimentos main

# antes de cada experimento: trazer o que entrou em main
git -C ~/dev/ai-coding-agent-profiles-experimentos merge --ff-only main

# pré-registro: commitar o manifesto ANTES da execução registrada
git -C ~/dev/ai-coding-agent-profiles-experimentos add docs/experimentos/EXP-NNNN-<slug>
git -C ~/dev/ai-coding-agent-profiles-experimentos commit -m 'exp(EXP-NNNN): pre-registro'

# depois do resultado escrito: levar a main
git -C ~/dev/ai-coding-agent-profiles merge --ff-only experimentos
```

Se o `--ff-only` recusar porque `main` andou, `git merge experimentos` resolve sem conflito: as
duas frentes não tocam os mesmos arquivos.

Dentro do worktree:

```bash
python3 skills/experimento-controlado/scripts/rodar-experimento.py \
    docs/experimentos/EXP-NNNN-<slug>/experimento.json
```

A primeira linha da saída diz `pré-registrado: sim (<commit>)`. Se disser `não`, a execução é
exploratória e não decide nada.
