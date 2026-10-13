<!-- Caminho relativo: docs/recusados/guarda-de-comando-por-substring-sem-ressalva.md -->

# Guarda de comando por substring, sem ressalva de leitura

**O que foi pedido.** Adotar, como guarda de comando git, um hook que procura o texto do
comando perigoso em qualquer posição da linha e recusa. É a correção mais óbvia para a
indireção, e foi medida num mecanismo de terceiro que faz exatamente isso.

**Por que está fora.** Sem ressalva, substring recusa a **menção** junto com a **execução**.
Medido em 2026-10-12:

```
grep -rn "git push" docs/            → BLOQUEOU   (é leitura de documentação nossa)
echo "o agente nunca roda git push"  → BLOQUEOU   (é a própria regra sendo citada)
git commit -m "x"                    → PASSOU     (não estava na lista)
git -C . push origin main            → PASSOU     (a lista tinha "git push", com um espaço)
git  push origin main                → PASSOU     (espaço duplo quebra o padrão)
```

Uma guarda que impede ler as regras que ela aplica treina quem a usa a desligá-la. E lista de
literais sem normalização dá a sensação de cobertura com a cobertura do literal.

O que foi recusado é a guarda **sem ressalva**, não o casamento sem ancoragem. Esse é bom e
foi importado: `checar-comando-git.sh` ganhou uma segunda camada gananciosa, que quebra a linha
nos separadores de comando, dispensa segmento que começa por ferramenta de leitura e cobre os
seis vetores que a ancoragem por posição deixava passar. Autoteste em 25 recusas e 21
liberações, mais quatro lacunas declaradas.

**Condição de reabertura.** Nenhuma prevista para a forma sem ressalva. Se aparecer vetor que
só a substring crua pega — isto é, com o `git` precedido de caractere que a ressalva de leitura
dispensa —, o vetor entra no autoteste e a ressalva se estreita; a guarda crua continua fora.

**Pedidos anteriores.** 2026-10-12, na triagem de biblioteca de terceiros, item
`git-guardrails-claude-code`.

**Decidido em.** Triagem de 2026-10-12, com medição registrada no MT-24.
