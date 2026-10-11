<!-- Caminho relativo: docs/adr/0018-registro-de-recusados.md -->

# ADR 0018: Registro de conceitos recusados, indexado por conceito

- **Status:** Accepted
- **Data:** 2026-10-11
- **Decisores:** Iago Leal (mantenedor), com Claude Code
- **Tags:** governança, adr, triagem

## Contexto

Recusar é decisão, e hoje ela some. Quando um conceito é avaliado e descartado, o registro
vira prosa dentro de uma ADR cujo assunto é outro — recuperável só por quem lembra que aquela
ADR existe. Meses depois a mesma proposta volta, e é reavaliada do zero.

A diferença não é de conteúdo, é de **modo de acesso**: a ADR se busca por número e data; o
conceito recusado precisa ser buscado **por nome**, no momento em que alguém o propõe de novo.

## Decisão

> Um diretório **`docs/recusados/`**, um arquivo por conceito, nome do arquivo igual ao nome
> do conceito, indexado em `docs/recusados/README.md`. **A ADR continua guardando o evento de
> decisão**; o registro é índice e gancho de triagem, e cita a ADR que decidiu.

### Seções fixas

```markdown
# <conceito>

**O que foi pedido.** Uma frase, nos termos de quem pediu.
**Por que está fora.** O raciocínio, delimitando o que exatamente está recusado.
**Condição de reabertura.** O fato novo que mudaria a resposta, ou "nenhuma prevista".
**Pedidos anteriores.** Uma linha por vez que o conceito voltou, com data.
**Decidido em.** ADR NNNN, ou "sem ADR" quando a recusa não gerou decisão arquitetural.
```

"Pedidos anteriores" é o campo que faz o registro render: a recorrência vira dado, e
reincidência passa a ser mensurável em vez de impressão.

## Consequências

**Positivas.** A recusa fica recuperável pelo nome que a pessoa usa ao propor. A triagem ganha
um passo barato: bater no registro fecha o assunto em uma linha, citando a ADR. E o registro
vira a segunda perna da barra de admissão (ADR 0019), que hoje não existe.

**Negativas.** Mais um lugar para manter sincronizado. O risco conhecido é registro que vira
cemitério de ideias sem condição de reabertura, transformando recusa circunstancial em dogma —
por isso a condição de reabertura é **seção obrigatória**, e "nenhuma prevista" é uma resposta
que precisa ser escrita, não omitida.

**Retroativo.** As recusas já tomadas e enterradas em prosa de ADR são recuperadas aos poucos,
quando o conceito reaparecer — não há mutirão de arqueologia.
