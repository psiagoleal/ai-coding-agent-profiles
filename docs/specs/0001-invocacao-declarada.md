<!-- Caminho relativo: docs/specs/0001-invocacao-declarada.md -->

# Spec 0001 — Invocação declarada nas skills

- **Status:** Aceita
- **Data:** 2026-10-11
- **Decide a partir de:** ADR 0016
- **Tickets:** a criar — ver §6

## Problema

Uma descrição serve duas audiências com necessidades opostas, e o custo apareceu em produção:
um catálogo de 105 skills somou 55,3 KB contra teto de 50 KB, e dezesseis skills nossas
sumiram do catálogo sem aviso ao modelo. A causa do descarte foi posição na ordenação, não
tamanho — a nossa média é 494 B contra 548 B das demais.

O teto de 50 KB é observação de **um** harness, o único que avisou. O acervo inteiro — 169
skills, 83,2 KB — é 1,66× esse teto, e por isso quem fecha o orçamento é a seleção na
instalação (ADR 0022), não esta spec. Esta spec entrega folga dentro do conjunto já
selecionado, e tira a audiência humana do contexto.

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

## Testes

1. Skill com `invocacao: humano` instalada para Claude Code sai com
   `disable-model-invocation: true`.
2. A mesma skill instalada para Codex sai com `policy.allow_implicit_invocation: false`.
3. A mesma skill instalada para harness sem mecanismo **gera aviso** que a nomeia.
4. Skill sem o campo **reprova** a instalação, nomeando o arquivo.
5. Valor fora do conjunto reprova, nomeando o valor.
6. O instalador reporta, por harness, quantas skills não puderam ser traduzidas.
7. Medição antes e depois: a soma de descrição das skills `modelo` cai conforme o esperado.

## Fora de escopo

- **Reescrever as descrições.** A separação de audiência vem depois, por spec própria.
- **A seleção na instalação.** É a alavanca que fecha o orçamento (ADR 0022, MT-43), e tem
  spec própria. Esta spec não fecha o orçamento sozinha, e a ADR 0016 declara isso.
- **Medir o que cada harness faz com catálogo acima do teto.** É o MT-44, e é pré-requisito
  para saber contra qual teto medir em cada destino — aqui se mede contra o único observado.
- **Fronteira negativa nas descrições.** É o MT-29, e tem conflito de orçamento próprio.
- **Mecanismo para os três harness sem suporte.** Aqui só se declara a lacuna.

## Verificação da própria spec

O ganho previsto é de 48,9 a 52,6 KB conforme a fração convertida, contra 55,3 KB hoje, **no
catálogo de campo de 105 skills e contra o teto daquele harness**. **Se a medição depois da
implementação ficar fora dessa faixa, a spec errou** e a diferença precisa ser explicada antes
de seguir para a seleção.

A faixa não cruza para baixo de 50 KB em nenhuma fração. Isso é previsão, não defeito: se a
medição *fechar* o orçamento, a spec também errou — e o que precisa ser reexaminado é a conta
de quantas skills do catálogo são nossas.
