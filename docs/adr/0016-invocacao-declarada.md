<!-- Caminho relativo: docs/adr/0016-invocacao-declarada.md -->

# ADR 0016: Invocação declarada na skill, traduzida por harness

- **Status:** Accepted — revisada em 2026-10-11 após revisão do mantenedor
- **Data:** 2026-10-11
- **Decisores:** Iago Leal (mantenedor), com Claude Code
- **Tags:** skills, catálogo, portabilidade, instalador

## Contexto

Toda skill nossa carrega **uma** descrição, que tenta servir duas audiências ao mesmo tempo:
o humano que escolhe o que invocar e o modelo que decide sozinho se aquilo se aplica. As duas
querem coisas opostas — o humano quer um resumo, o modelo quer gatilhos.

O custo disso deixou de ser teórico. Em uso real (2026-10-09), um catálogo de 105 skills
instaladas somou **55,3 KB de descrição contra um teto de 50 KB**, e dezesseis skills nossas
foram **descartadas do catálogo** por estourarem o orçamento. Não fomos descartadas por sermos
grandes: a média nossa é 494 B contra 548 B das demais. Fomos descartadas por posição, por
ordenarmos no fim da lista. O descarte foi **silencioso para o modelo**: ele simplesmente
deixou de ver dezesseis capacidades.

### O acervo, medido, e o que a medição decide

O acervo é **um só**, distribuído por dois repositórios. A diferença entre eles é apenas se o
material pode ser exposto em repositório público; não é diferença de dono, de qualidade nem de
estado. Medido em 2026-10-11:

| | skills | descrição de catálogo | média |
|---|---|---|---|
| `ai-coding-agent-profiles` | 35 | 18,0 KB | 527 B |
| `ai-coding-agent-profiles-privado` | 134 | 65,2 KB | 497 B |
| **acervo** | **169**, sem nome repetido | **83,2 KB** | 505 B |

O acervo inteiro é **1,66× o único teto que já observamos**, antes de qualquer importação. Não
existe fração de conversão de invocação que faça 169 skills caberem em 50 KB, e não existe poda
que faça isso sem destruir o acervo. Instalar o acervo inteiro em um projeto nunca foi a
intenção, e a medição mostra que também nunca foi possível.

Isso recoloca o problema: **o orçamento de catálogo é um problema de instalação, não de
acervo.** O acervo cresce; o que é instalado por projeto é o que precisa caber.

### O teto de 50 KB é uma observação, não uma constante

O número vem de **um** harness, que avisou o corte. Os outros nunca disseram nada, e isso
admite duas leituras opostas: ou não têm limite, ou cortam em silêncio. Qual das duas é
verdade está **não medido** — e a segunda leitura é exatamente o modo de falha que esta ADR
existe para corrigir, agora um nível acima: não a skill descartada sem aviso, mas o harness
que descarta sem aviso. Até a medição existir, todo cálculo contra "50 KB" vale para aquele
harness e para nenhum outro.

### A biblioteca de terceiros

A biblioteca analisada resolve a parte de audiência declarando a invocação por skill: 23 de 38
(61%) são alcançáveis apenas pelo humano e não entram no catálogo do modelo. A descoberta
humana sai do contexto e vai para o índice e a documentação.

## Decisão

> Cada `SKILL.md` declara **`invocacao: humano | modelo`** no frontmatter. O instalador
> traduz essa semântica para o mecanismo de cada harness, e **avisa** quando o harness de
> destino não tem como honrá-la.

### 1. O campo é nosso, o flag é do harness

```yaml
name: gates-de-conclusao
invocacao: modelo
description: ...
```

| Harness | Tradução na instalação |
|---|---|
| Claude Code | `disable-model-invocation: true` quando `invocacao: humano` |
| Codex | `policy.allow_implicit_invocation: false` em `agents/openai.yaml` |
| demais | sem mecanismo equivalente — o instalador **avisa**, nomeando as skills afetadas |

Adotar o flag de um harness como mecanismo acoplaria a nossa governança a ele. Com cinco
harness atendidos, três ignorariam o interruptor e a distinção degradaria **em silêncio** —
exatamente o modo de falha que esta ADR existe para corrigir.

### 2. A descrição segue a invocação

- **`invocacao: humano`** — uma linha, resumo, sem gatilhos. Não entra no catálogo do modelo.
- **`invocacao: modelo`** — gatilhos concretos e positivos ("Use quando…"), e fronteira
  negativa **só** quando houver confusão real com outra skill.

Campo ausente é **erro de instalação**, não `modelo` por omissão. Cair no padrão é como uma
skill cara silenciosamente vira barata, e ninguém percebe.

### 3. Esta ADR é uma das três alavancas, e não é a primeira

O orçamento tem três alavancas, e a ordem entre elas vem do que a medição do acervo mostrou:

1. **Seleção na instalação** — derivar do tipo de projeto, da stack e dos requisitos quais
   skills do acervo entram. É estrutural: é a única que escala com um acervo que cresce.
   Decidida à parte, na **ADR 0022**.
2. **Invocação declarada** — esta ADR. Reduz o catálogo do modelo *dentro* do conjunto já
   selecionado, e tira a audiência humana do contexto.
3. **Poda** — remover o que está obsoleto ou duplicado, **pelo mérito do item**, nunca para
   abrir espaço. Skill importada para o acervo é nossa (ADR 0021), e não é passivo a ser
   cortado quando o orçamento aperta.

## Consequências

**Positivas.** O orçamento do catálogo passa a ser governável por decisão, não por sorte de
ordenação. A descrição deixa de ter duas audiências. O aviso do instalador torna visível a
cobertura real por harness.

**Negativas e limites declarados.** Medimos o ganho **dentro do catálogo de campo**, de 105
skills, e ele **não fecha sozinho**: das 17 skills nossas naquele catálogo, converter de 40% a
70% leva o total de 55,3 KB para algo entre 48,9 e 52,6 KB — **à linha dos 50 KB, não
confortavelmente abaixo**. O excesso é 5,3 KB e as nossas 17 somam 8,2 KB. A conta é essa
porque a conversão só pode descontar o que é nosso; os outros 88 itens do catálogo não têm o
campo.

| nossas convertidas para `humano` | catálogo resultante |
|---|---|
| 40% (7 de 17) | 51,2 – 52,6 KB — ainda acima |
| 53% (9 de 17) | 50,2 – 51,7 KB — ainda acima |
| 60% (10 de 17) | 49,8 – 51,2 KB — na linha |
| 70% (12 de 17) | 48,9 – 50,2 KB — na linha |

Quem fecha o orçamento é a alavanca 1, a seleção. Esta ADR entrega folga e tira a audiência
humana do caminho; não entrega o fechamento, e não deve ser implementada esperando que entregue.

Três de cinco harness ficam sem enforcement até terem mecanismo. Isso é declarado no aviso, e
não deve ser lido como proteção.

**Verificação.** O instalador reprova skill sem `invocacao`, e reporta por harness quantas
skills não puderam ser traduzidas.
