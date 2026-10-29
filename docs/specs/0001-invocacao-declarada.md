<!-- Caminho relativo: docs/specs/0001-invocacao-declarada.md -->

# Spec 0001 — Invocação declarada nas skills

- **Status:** Aceita — reescrita em 2026-10-29 no formato da ADR 0024 (critérios em EARS, com
  prova) e criticada em contexto limpo; o decidido em 2026-10-11 não mudou, salvo a frase do
  critério 8 que contradizia a ADR 0016
- **Data:** 2026-10-11
- **Decide a partir de:** ADR 0016; a parte de instalador, ADR 0023 §6
- **Tickets:** [MT-56](../tickets/MT-56.md) (campo nas skills) → [MT-57](../tickets/MT-57.md)
  (reprovação no instalador) · [MT-55](../tickets/MT-55.md) (tradução por harness) →
  [MT-58](../tickets/MT-58.md) (medição)

## Problema

Uma descrição serve duas audiências com necessidades opostas, e o custo apareceu em produção:
um catálogo de 105 skills somou 55,3 KB contra teto de 50 KB, e dezesseis skills nossas
sumiram do catálogo sem aviso ao modelo. A causa do descarte foi posição na ordenação, não
tamanho — a nossa média é 494 B contra 548 B das demais.

O teto de 50 KB é observação de **um** harness, o único que avisou. O acervo inteiro — 169
skills, 83,2 KB — é 1,66× esse teto, e por isso quem fecha o orçamento é a seleção na
instalação ([spec 0003](0003-orcamento-de-contexto.md)), não esta spec. Esta spec entrega folga
dentro do conjunto já selecionado, e tira a audiência humana do contexto.

## Solução

Declarar `invocacao: humano | modelo` em cada `SKILL.md` e traduzir no instalador para o
mecanismo de cada harness, avisando onde não houver mecanismo.

## Histórias

1. **Como mantenedor**, quero marcar uma skill como alcançável só por mim, para que ela não
   consuma o orçamento de catálogo do modelo.
2. **Como mantenedor**, quero que o instalador me diga quais harness não honram a marcação,
   para não confundir declaração com proteção.
3. **Como agente**, quero um catálogo que caiba no orçamento, para não perder capacidades em
   silêncio.
4. **Como mantenedor**, quero que skill sem o campo reprove a instalação, para que o padrão
   nunca seja escolhido por omissão.

## Decisões de implementação

| Decisão | Escolha | Por quê |
|---|---|---|
| Nome do campo | `invocacao` | português, como o resto do frontmatter nosso |
| Valores | `humano`, `modelo` | fechado; terceiro valor é erro |
| Ausência | erro de instalação | cair no padrão esconde a decisão |
| Flag do harness | gerado na instalação | não acoplar governança a um harness |
| Harness sem mecanismo | aviso nomeando as skills | declarar a cobertura real |
| Adaptador da skill `humano` | diretório com `SKILL.md` gerado, resto por symlink | symlink não carrega cabeçalho por harness (ADR 0023 §6) |
| Ordem de entrega | campo em todas as skills **antes** da reprovação | reprovar antes de marcar quebraria toda instalação existente |

## Critérios de aceite

Prova: asserção nomeada em `scripts/testar-instalador.sh`, salvo onde dito.

Termos: **corpo** é tudo depois do frontmatter do `SKILL.md` neutro. **Harness sem mecanismo**
é o que não declara tradução de `invocacao` na tabela por agente da
[spec 0002](0002-instalacao-por-agente.md). **As duas fontes** são o acervo público e a fonte
privada; `SKILL.md` gerado em adaptador não conta.

| # | Critério | Prova | Ticket |
|---|---|---|---|
| 1 | QUANDO uma skill com `invocacao: humano` é instalada para Claude Code, o instalador DEVE gerar o `SKILL.md` do adaptador com `disable-model-invocation: true` e o corpo idêntico ao neutro | asserção "invocacao humano → claude" | MT-55 |
| 2 | QUANDO a mesma skill é instalada para Codex, o instalador DEVE gerar `policy.allow_implicit_invocation: false` | asserção "invocacao humano → codex" | MT-55 |
| 3 | SE o harness de destino não tem mecanismo de invocação declarada, ENTÃO o instalador DEVE avisar nomeando cada skill `humano` não traduzida | asserção "invocacao humano → harness sem mecanismo" | MT-55 |
| 4 | SE um `SKILL.md` não tem o campo `invocacao`, ENTÃO o instalador DEVE reprovar com código diferente de zero, nomeando o arquivo | asserção "skill sem invocacao reprova" | MT-57 |
| 5 | SE o valor de `invocacao` está fora de `{humano, modelo}` — inclusive vazio, nulo, lista ou chave repetida —, ENTÃO o instalador DEVE reprovar nomeando o arquivo e o valor | asserção "invocacao inválida reprova", com os quatro formatos | MT-57 |
| 6 | Ao fim de toda instalação, o instalador DEVE imprimir, por harness, quantas skills `humano` não puderam ser traduzidas | asserção "relatório de não traduzidas" | MT-55 |
| 7 | Todo `SKILL.md` das duas fontes do acervo DEVE ter `invocacao` com valor válido | `scripts/checar-invocacao.sh` sobre as duas fontes sai 0 | MT-56 |
| 8 | DEPOIS do MT-56 e do MT-55, a soma das descrições das skills `modelo` no catálogo de campo de 105 skills (o de 2026-10-09, reconstituído no MT-58) DEVE cair para a subfaixa que a tabela da ADR 0016 dá para a fração efetivamente convertida | medição antes e depois, com o comando, registrada no MT-58 e comparada à subfaixa | MT-58 |

O critério 8 é a verificação da própria spec: **fora da subfaixa, a spec errou**, e a diferença
é explicada antes de seguir para a seleção. A faixa inteira vai de 48,9 KB (70% convertidas) a
52,6 KB (40%), e fica **à linha dos 50 KB, não confortavelmente abaixo**, como diz a ADR 0016.

> Corrigido em 2026-10-29: o texto de 2026-10-11 dizia que a faixa "não cruza para baixo de
> 50 KB em nenhuma fração", o que contradiz a tabela da ADR 0016 (60% e 70% chegam a 49,8 e
> 48,9 KB). Achado pela crítica em contexto limpo.

## Fora de escopo

- **Reescrever as descrições.** A separação de audiência vem depois, por spec própria.
- **A seleção na instalação.** É a alavanca que fecha o orçamento — [spec 0003](0003-orcamento-de-contexto.md).
- **Medir o que cada harness faz com catálogo acima do teto.** MT-44, na spec 0003. Aqui se
  mede contra o único teto observado.
- **Fronteira negativa nas descrições.** MT-29, na spec 0003, com conflito de orçamento próprio.
- **Mecanismo para os harness sem suporte.** Aqui só se declara a lacuna.

## Decisões pendentes

Nenhuma. A classificação de cada skill em `humano` ou `modelo` é trabalho do MT-56, com a lista
proposta aprovada pelo mantenedor antes de entrar.
