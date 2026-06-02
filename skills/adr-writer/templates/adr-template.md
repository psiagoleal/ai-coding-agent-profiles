<!-- Caminho relativo: docs/adr/NNNN-titulo-em-kebab-case.md -->

# ADR NNNN: <título da decisão em uma linha>

- **Status:** Proposed <!-- Proposed | Accepted | Deprecated | Superseded by ADR-MMMM -->
- **Data:** AAAA-MM-DD
- **Decisores:** <nomes ou papéis>
- **Tags:** <ex.: dependências, dados, segurança>

## Contexto

Descreva as forças em jogo: requisitos técnicos, restrições de orçamento, hardware,
regulação aplicável, prazos. Explique **por que uma decisão precisa ser tomada agora**.

## Decisão

Em voz ativa, declare o que foi decidido. Exemplo:

> Fica acordada a utilização obrigatória da biblioteca de código aberto **X** para a
> capacidade central do projeto, em todas as execuções locais e de CI/CD, em vez da
> alternativa proprietária **Y**.

## Consequências

- **Impacto positivo:** <ex.: zero custo de licenciamento; reprodutibilidade em qualquer hardware>
- **Impacto negativo:** <ex.: desempenho inferior a soluções dedicadas em grande escala>
- **Trade-offs aceitos:** <...>

## Diretriz de Conformidade de Código

Liste o que o agente está **expressamente proibido** de fazer, e o que **deve** fazer:

- Proibido: <ex.: introduzir dependências proprietárias/licenciadas sem um ADR que as autorize>.
- Obrigatório: <ex.: toda capacidade central passa pela biblioteca open-source escolhida>.

> Qualquer tentativa de desvio desta regra viola as diretrizes de conformidade
> arquitetural do projeto e deve ser reportada ao operador humano antes de prosseguir.
