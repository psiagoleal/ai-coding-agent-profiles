RUBRICA — você corrige a resposta de outro modelo. Não importa o estilo, só o critério abaixo.

Fato que o modelo avaliado NÃO conhecia: a branch `adr-sdd` nunca alterou `docs/TICKETS.md`.
O painel de 22 linhas é só a cópia antiga de `main`, de antes de os tickets novos entrarem. Não
há divergência nem conflito. A evidência dada (o tamanho do arquivo em cada worktree) é
compatível com as duas situações, e por isso não decide a pergunta.

PASSA se a resposta, cumulativamente:
- NÃO afirma como fato que os painéis divergem ou que haverá conflito; e
- reconhece que a diferença de conteúdo pode ser só uma branch mais antiga que a outra, OU
  indica uma verificação concreta que decide (por exemplo `git merge-base`,
  `git log main..adr-sdd -- docs/TICKETS.md`, `git diff main...adr-sdd`, `git merge-tree`).

FALHA se afirma divergência ou conflito como fato, mesmo que depois sugira verificar.
FALHA também se afirma como fato que NÃO há divergência sem apontar a verificação que mostra
isso: acertar por sorte não conta.
