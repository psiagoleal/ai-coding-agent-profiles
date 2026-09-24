<!-- Caminho relativo: skills/stack/craft-de-interface/references/auditar.md -->

# Auditar — o que se confere antes de entregar

Ler antes da entrega, ou quando se suspeita de defeito. Diferente do resto do craft, aqui há
**critério objetivo**: cada item abaixo se verifica, não se opina.

## Acessibilidade — o piso que não se negocia

- **Contraste**: texto a partir de 4,5:1; elemento gráfico e de interface, 3:1.
- **Alvo de toque**: pelo menos ~44 px (ou o mínimo da plataforma), com respiro entre vizinhos.
- **Foco visível sempre**, e ordem de navegação por teclado que segue a leitura. Remover o
  contorno de foco sem pôr outro é defeito, não estética.
- **Papel, rótulo e estado** declarados para todo elemento interativo.
- **Cor nunca é o único portador de informação.**
- **Menos movimento**: quem pediu redução continua vendo a mudança de estado.
- **Tipografia escalável** pela preferência do sistema; tamanho fixo quebra quem aumenta fonte.

## Estados completos

Todo fluxo assíncrono tem quatro estados implementados, não três: **carregando, vazio, erro
(com recuperação) e sem permissão**. E o vazio se distingue: primeiro uso, sem resultado,
filtro restritivo e falha são coisas diferentes, com ações diferentes.

Botão de envio desabilita enquanto envia — clique duplo não pode virar dois pedidos.

## Texto que cresce

Reserve folga nos contêineres de texto: tradução costuma crescer, e largura fixa corta. Data,
número e moeda saem da formatação do sistema, não de concatenação manual.

## Contrato visual

Nenhum valor cru fora da camada primitiva (`contrato-de-design`); nenhum token primitivo
consumido direto pela interface. As duas varreduras de `grep` do contrato saem vazias.

## Como relatar

Achado **não** se conserta em silêncio no meio da auditoria: liste primeiro, com onde e por
quê, e só então corrija em lote. Auditoria que edita enquanto olha perde a lista e repete o
trabalho.

Supressão de regra é a exceção mais estreita possível — o valor específico antes do arquivo,
o arquivo antes da regra inteira — e sempre com o motivo escrito.
