<!-- Caminho relativo: docs/specs/0003-orcamento-de-contexto.md -->

# Spec 0003 — Orçamento do que o agente carrega ao abrir: catálogo e arquivo de regra

- **Status:** Rascunho — **duas decisões pendentes** (ver fim); criticada em contexto limpo em
  2026-10-29, achados incorporados. O critério 7 só ganha redação final com a decisão B
- **Data:** 2026-10-29
- **Decide a partir de:** ADR 0022; ADR 0016; ADR 0023 §1 (o manifesto onde a seleção é gravada)
- **Tickets:** [MT-44](../tickets/MT-44.md) (medir o teto) · [MT-43](../tickets/MT-43.md)
  (derivar a seleção, depois do MT-52) · [MT-29](../tickets/MT-29.md) (fronteira nas
  descrições, depois do MT-44) · [MT-31](../tickets/MT-31.md) (catálogo fora do arquivo de regra)

## Problema

Ao abrir uma sessão, o agente carrega duas coisas antes de ler qualquer pedido: o catálogo de
descrições das skills e o arquivo de regra do projeto. As duas cresceram sem medida.

- O acervo tem 169 skills e 83,2 KB de descrição (medido em 2026-10-11). O único teto observado
  é 50 KB, num harness, que **descartou dezesseis skills nossas em silêncio para o modelo**. Os
  outros quatro harness nunca avisaram nada, e isso pode querer dizer que não têm teto ou que
  cortam sem dizer.
- O arquivo de regra do perfil empresa tem 17.303 caracteres, contra cerca de 9.000 dos harness
  comparados, e um quinto dele é o catálogo de skills repetido em prosa (medido em 2026-10-04).
- Uma descrição em 35 diz quando **não** usar a skill. É o único roteamento que existe, e sem
  fronteira o disparo pega a skill errada. Mas a fronteira custa cerca de 58 B por skill, num
  orçamento que já estoura.

## Solução

Medir o teto de cada harness. Instalar em cada projeto só o que ele usa, derivado da árvore e
gravado com o motivo de cada skill. Relatar o tamanho resultante contra o teto do destino. Só
então gastar orçamento com fronteira nas descrições. Tirar o catálogo do arquivo de regra.

## Histórias

1. **Como agente**, quero ver todas as skills instaladas, para não perder capacidade sem saber.
2. **Como mantenedor**, quero saber por que cada skill está num projeto, para repetir ou
   corrigir a instalação seis meses depois.
3. **Como mantenedor**, quero saber o teto de cada harness, medido, para não confundir silêncio
   com ausência de limite.
4. **Como agente**, quero descrições que digam quando não usar a skill, para disparar a certa.
5. **Como agente**, quero um arquivo de regra curto, com gatilho → skill, para gastar contexto
   com o pedido e não com o índice.

## Decisões de implementação

| Decisão | Escolha | Onde |
|---|---|---|
| Precedência dos sinais | manifesto do projeto > detecção da árvore > pergunta; ambiguidade pergunta | ADR 0022 §1 |
| Registro | seleção gravada com o `sinal` de cada skill, no manifesto da instalação | ADR 0022 §2, ADR 0023 §1 |
| Núcleo de governança | entra sempre; derivação só atua sobre o resto | ADR 0022 §3 |
| Mapa sinal → categoria | em dado, não em código | MT-43 |
| Poda do acervo | não se faz: skill importada é nossa | ADR 0021 |
| Harness sem limite observado | marcado "não observado até N", nunca "sem limite" | MT-44 |
| Ordem | teto medido (MT-44) antes da fronteira nas descrições (MT-29) | MT-29 |
| Catálogo acima do teto | avisa com o excesso; não reprova nem corta — mede, como manda a ADR | ADR 0022 §4 |

## Critérios de aceite

| # | Critério | Prova | Ticket |
|---|---|---|---|
| 1 | Para cada um dos cinco harness atendidos, DEVE existir linha com o teto medido **ou** "não observado até N", a forma do corte quando houver (posição, tamanho, ordem), aviso ou silêncio, e o comando que produziu a linha | tabela em `docs/interop/`; o revisor reexecuta o comando de pelo menos uma linha por harness | MT-44 |
| 2 | SE um harness não cortou até o maior tamanho testado, ENTÃO a tabela DEVE registrar "não observado até N", e NÃO DEVE registrar "sem limite" | `grep -i "sem limite"` na tabela não encontra nada | MT-44 |
| 3 | QUANDO três projetos de stacks diferentes são instalados sem `--skills`, o instalador DEVE produzir três seleções diferentes, todas com o núcleo de governança | asserção "três stacks, três seleções" em `testar-instalador.sh` | MT-43 |
| 4 | Toda skill no manifesto DEVE ter `sinal` em `{nucleo, pedido, detectado:<marcador>, perguntado}` | asserção "toda skill tem sinal" | MT-43 |
| 5 | SE não há manifesto do projeto e a detecção é ambígua ou vazia, ENTÃO o instalador DEVE perguntar (ou recusar sem terminal interativo), e NÃO DEVE escolher padrão em silêncio | asserção "detecção ambígua pergunta" | MT-43 |
| 6 | Ao fim da instalação, o instalador DEVE imprimir, por harness de destino, o tamanho de catálogo resultante e um veredito: `cabe`, `excede em X KB` ou `teto não medido` | asserção "tamanho e veredito relatados", com teto fabricado nos três casos | MT-43 |
| 6a | SE o catálogo excede o teto medido, ENTÃO o instalador DEVE avisar com o excesso e as skills que ficariam por último na ordenação, e NÃO DEVE reprovar a instalação nem cortar skill sozinho | asserção "excesso avisa e não corta" | MT-43 |
| 7 | QUANDO a árvore mudou de stack desde a última instalação, o `--update` DEVE seguir a regra da decisão pendente B, testada | asserção "reinstalação após troca de stack" | MT-43 |
| 8 | O lint de descrição DEVE reprovar, nomeando-a, a skill cuja descrição não tem nenhum dos dois marcadores de fronteira ("NÃO use para", "use para") ou passa do teto por descrição, fixado no MT-29 a partir da medição do MT-44; depois da correção, DEVE passar e entrar no CI | `lint-descricoes --autoteste` reprova descrição fabricada nos dois casos; `lint-descricoes` sobre o acervo sai 0; passo no CI | MT-29 |
| 9 | O arquivo de regra do perfil empresa DEVE ficar abaixo de 10.000 caracteres sem perder nenhum nome de skill | `wc -m` e comparação das duas listas de nomes | MT-31 |

## Fora de escopo

- **Invocação declarada** (`invocacao: humano`): dá folga dentro do conjunto selecionado, mas
  não fecha o orçamento. [Spec 0001](0001-invocacao-declarada.md).
- **Reescrever o corpo das skills** e as seções de segurança e de fluxo do arquivo de regra
  (MT-32).
- **Separar descrição para humano e para modelo.** Spec futura, citada pela spec 0001.

## Decisões pendentes

A ADR 0022 deixou duas decisões em aberto. O MT-43 escolhia uma delas em "Fora de escopo", e
é isso que esta seção substitui. **A spec não passa a Aceita sem as duas.**

**A. Granularidade do mapa stack → acervo.**
Recomendação: **por categoria de diretório** (`stack/`, `dominio/`, …), que já existe nas duas
fontes e não custa manutenção. A marcação dentro de cada `SKILL.md` é mais fina, mas obriga a
manter um campo novo em 169 arquivos. Ela pode vir depois, se a categoria se mostrar grossa
demais em campo.

**B. Reinstalação quando a árvore mudou de stack.**
Recomendação: **re-derivar, acrescentar o que entrou e imprimir o plano de remoção do que
saiu**, sem apagar. É a mesma regra da troca de agente (ADR 0023 §5), e mantém o instalador
sem nunca remover arquivo do alvo. "Só acrescentar" deixa skill morta no catálogo, gastando o
orçamento que esta spec existe para proteger.
