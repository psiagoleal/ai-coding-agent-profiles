<!-- Caminho relativo: docs/planos/decisao-tipada.md -->

# Plano — decisão tipada como camada de roteamento

- **Status:** rascunho para discussão · 2026-09-25
- **Escopo:** este framework **e** o `agentry`, que podem ser usados juntos ou separados

## O que é, em uma frase

Uma classe de modelo que devolve **decisão tipada com probabilidade calibrada** em vez de
texto: escolha entre N opções, sim/não, ou nota — em uma passada, para software consumir.

O uso que interessa aqui é **roteamento**: decidir, antes de gastar, qual modelo deve receber
a tarefa.

## O que foi verificado (2026-09-25)

| Alternativa | O que é | Licença | Ponto de atenção |
|---|---|---|---|
| **Jev** (TypeSafe AI) | API hospedada, "System One Model", treinado por RLCD | proprietária, **fila de contas** | "zero alucinação" é alegação de marketing: o modelo não inventa *formato*, mas erra *decisão* |
| **OpenJev** | 27 B, pesos abertos, decisão tipada até 52 opções | **CC BY-NC 4.0** | **não-comercial** — inutilizável em trabalho da empresa |
| **Laya** (Convai) | ModernBERT-large 395 M + cabeça de decisão | **Apache 2.0** | a acurácia publicada (0,766) vem de ajuste nos dados do próprio *benchmark*; **zero-shot 0,362 contra 0,461 do baseline trivial** |

Duas conclusões que mudam o plano:

1. **A licença separa as opções por perfil.** OpenJev não pode ser usado em projeto comercial;
   Laya pode. O perfil do repositório (`empresa`, `externo-confidencial`, `pessoal`) decide o
   que é permitido, como já fazemos com egresso.
2. **Pesos abertos não são substituto pronto.** Laya zero-shot é **pior que o baseline
   trivial**. Sem ajuste no nosso domínio, um roteador baseado nela decide pior que "mande
   sempre para o modelo padrão".

## O princípio que organiza o desenho

> **Roteador é uma hipótese até ser medido contra o baseline trivial.**

O baseline trivial é: mandar tudo para o modelo padrão. Um roteador só se adota se, num
conjunto rotulado de tarefas reais, ele **ganha do baseline** em custo sem perder qualidade —
e se a probabilidade que ele devolve **significa** o que diz.

Três medidas, nesta ordem:

- **Acerto contra o baseline** — não contra o acaso.
- **Calibração** — entre as decisões com confiança 0,8, cerca de 80% acertam? Sem isso, o
  limiar de escalada é chute.
- **Custo e latência ponta a ponta**, incluindo o roteador. Roteador que economiza 40% do
  token e acrescenta 300 ms pode não valer.

## A regra de escalada

O valor não está no rótulo; está na **probabilidade**. O desenho é:

```
decisão tipada  →  confiança ≥ limiar ?  →  sim: roteia para o modelo barato
                                         →  não: cai para o modelo padrão
```

O limiar sai da medição de calibração, não de palpite. E a escalada é sempre para o **mais
capaz**, nunca o contrário.

## Divisão de responsabilidades

### Deste lado (framework)

- **Skill `decisao-tipada`**, neutra em relação a fornecedor — o mesmo caminho que tomamos com
  "OpenAI-compatible" em vez de amarrar ao gateway: quando uma decisão tipada bate uma chamada
  de chat, o contrato de entrada e saída, a regra de escalada e o protocolo de medição.
- **Guardas por perfil**: licença (não-comercial bloqueia perfil `empresa`) e egresso (pesos
  locais = `local-only`; API hospedada = nuvem, com as regras que já temos).
- **Gabarito**: como montar o conjunto rotulado a partir de tarefas reais, e o comando que
  mede acerto, calibração e custo. É o mesmo mecanismo do MT-7.

### Do lado do `agentry`

O que só o runtime pode fazer — e o desenho é de quem conhece o código:

- Onde a escolha de modelo acontece hoje, e o que consumiria uma decisão tipada.
- Abstração de provedor: endpoint HTTP (vLLM, TEI, API hospedada) e/ou execução local.
- Classe de egresso por provedor, coerente com o que já existe lá.
- Telemetria: registrar `(tarefa, decisão, confiança, modelo escolhido, resultado)` — é o que
  alimenta o gabarito. **Sem esse registro, a medição nunca acontece.**

### Contrato comum

O mesmo esquema de decisão dos dois lados, para que **um único gabarito** meça os dois:

```json
{"pergunta": "<texto>", "opcoes": ["a", "b"], "entrada": "<conteúdo>"}
{"escolha": "a", "probabilidade": 0.83, "modelo": "<id>", "ms": 34}
```

## Ordem sugerida

| # | Passo | Quem | Por que primeiro |
|---|---|---|---|
| 1 | Definir o contrato comum e o formato do gabarito | os dois | Sem ele, cada lado mede coisa diferente |
| 2 | Registrar decisões reais de roteamento (mesmo que heurísticas) | `agentry` | O gabarito precisa de dados reais, não sintéticos |
| 3 | Medir o baseline trivial | os dois | É o número que qualquer roteador precisa bater |
| 4 | Provar com um provedor só (Laya, Apache 2.0, local) | `agentry` | Licença livre e custo zero para experimentar |
| 5 | Skill `decisao-tipada` com o que a medição mostrar | framework | Escrever a regra **depois** do número, não antes |
| 6 | Jev hospedado, se e quando a conta sair | os dois | Comparação contra o mesmo gabarito |

## O que **não** fazer

- Adotar roteador sem gabarito — é trocar custo conhecido por erro desconhecido.
- Usar OpenJev em qualquer trabalho comercial (licença).
- Tratar "zero alucinação" como ausência de erro: decisão tipada erra **decisão**, e erra com
  confiança bem formatada.
- Amarrar as skills ao nome de um produto. O que entra no acervo é a **capacidade**; o
  fornecedor é configuração.
