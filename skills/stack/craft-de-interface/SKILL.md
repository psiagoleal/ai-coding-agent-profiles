---
name: craft-de-interface
description: >-
  Craft visual de interface em quatro operações — descobrir, estruturar, refinar
  e auditar — independentes de framework, com o playbook de cada uma lido só
  quando ela é pedida e um piso de qualidade lido só antes de editar. Aciona ao
  criar ou melhorar tela, ao pedir "deixe mais bonito", "revise a UI", "isso
  está confuso", antes de entregar interface, e quando a tela funciona mas não
  convence. NÃO usar para tokens e paleta (→ contrato-de-design) nem para
  escrever o componente na stack (→ criar-ui-sveltekit).
---

# craft-de-interface — quatro operações, não vinte e quatro verbos

"Deixe mais bonito" é o pedido menos acionável que existe. O que resolve não é adjetivo: é
saber **qual operação** está sendo pedida, porque cada uma preserva coisas diferentes.

## As duas leis

> **1. O brief vence o gosto do agente.** Estética fixada pelo usuário — época, material,
> fonte, paleta — é para ser honrada mesmo quando contraria o que o modelo acha bonito.
> Redirecionar um brief claro para a própria preferência é falha, não contribuição.
>
> **2. Refino preserva; redesenho substitui. Sem meio-termo.** Refino mantém identidade,
> comportamento, texto e tudo fora do escopo. Redesenho mantém a verdade do produto e trata a
> aparência antiga como evidência, não como base. **Polir o que foi descartado é desperdício
> dos dois lados.**

## As quatro operações

Identifique **uma** antes de tocar em qualquer coisa, e leia só o playbook dela:

| Operação | Quando | Playbook |
|---|---|---|
| **Descobrir** | Não há direção visual, ou ela não está escrita | `references/descobrir.md` |
| **Estruturar** | A tela tem os elementos certos na ordem errada | `references/estruturar.md` |
| **Refinar** | A estrutura está certa e falta acabamento | `references/refinar.md` |
| **Auditar** | Antes de entregar, ou quando se suspeita de defeito | `references/auditar.md` |

Se duas parecem caber, é porque o pedido tem duas etapas — faça na ordem da tabela, uma de
cada vez. Refinar antes de estruturar é maquiar um problema de hierarquia.

## Leia pouco, e na hora certa

- O playbook da operação entra **quando a operação é pedida**, não antes.
- `references/piso.md` — o piso de qualidade — entra **imediatamente antes de editar
  interface**. Em trabalho de diagnóstico, crítica ou planejamento, **não** carregue: ele
  custa contexto e não muda a decisão.
- O contrato visual (`docs/DESIGN.md`) e o `AGENTS.md` são o contexto do projeto. Se o
  `DESIGN.md` não existe e a operação é de aparência, pare: isso é `contrato-de-design`.

## Verificação com teto, não laço aberto

Interface não tem prova executável para "está bom". Então a verificação é **por passadas
limitadas**:

1. Construa por inteiro.
2. Inspecione **uma vez**, em lote — todas as larguras e temas de uma vez, não um por vez.
3. Corrija tudo o que a inspeção mostrou, em um lote só.
4. No máximo **mais uma** rodada de confirmação. Depois, pare.

Auto-QA aberto em interface é caro e converge para gosto. O que decide de verdade é o
`auditar`, que tem critério objetivo (contraste, alvo de toque, foco, estados), e a pessoa
que pediu. Ver `laco-de-correcao` para trabalho que **tem** prova executável — não é o caso
aqui.

## O que fica fora desta skill

- **Tokens, paleta, tipografia e escala** — `contrato-de-design` (o `docs/DESIGN.md`).
- **Como escrever o componente** — a skill da stack (`criar-ui-sveltekit`, `criar-app-tauri`).
- **Decisão de produto** — o que a tela precisa fazer é spec, não craft.

## O que você vai pensar

| O que você vai pensar | Por que não vale |
|---|---|
| "Vou modernizar isso do meu jeito" | O brief vence. Se o brief está errado, diga — não o contorne em silêncio. |
| "Aproveito e melhoro o resto da tela" | Toque só no alvo nomeado. O que não foi pedido preserva-se literalmente. |
| "Mais uma passada e fica perfeito" | A terceira passada custa e não converge. Pare no teto e entregue. |
| "Refino um pouco enquanto redesenho" | Meio-termo produz a pior das duas: nem identidade preservada, nem substituída. |
| "Isso é detalhe, ninguém nota" | Contraste, alvo de toque e foco não são detalhe; são o que faz a tela ser usável. |

## Ligação com o resto do acervo

`contrato-de-design` dá os tokens que este craft consome · `criar-ui-sveltekit` e
`criar-app-tauri` implementam · `perguntar-antes-de-construir` fecha as lacunas de brief antes
de começar · `pr-review-guard` confere o resultado no diff.

## Definição de pronto da skill

- [ ] A operação foi **nomeada** antes de qualquer edição, e só o playbook dela foi lido.
- [ ] O brief do usuário foi honrado, inclusive onde contraria a preferência do agente.
- [ ] Refino e redesenho não foram misturados.
- [ ] Nada fora do alvo nomeado foi alterado.
- [ ] `references/piso.md` foi lido antes de editar — e **não** em trabalho de diagnóstico.
- [ ] A verificação respeitou o teto de passadas.
- [ ] A operação `auditar` rodou antes de entregar, com os itens objetivos conferidos.
