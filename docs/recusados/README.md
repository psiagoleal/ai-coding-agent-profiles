<!-- Caminho relativo: docs/recusados/README.md -->

# Conceitos recusados

Um arquivo por conceito avaliado e descartado, buscável **pelo nome que quem propõe usa**.
Decisão em ADR 0018.

Leia antes de abrir ticket: bater num arquivo daqui fecha a proposta em uma linha. Se o seu
caso traz o fato novo que o campo **Condição de reabertura** pede, o ticket é legítimo — e
cite o arquivo, para a recorrência virar dado.

| Conceito | Resumo da recusa | Decidido em |
|---|---|---|
| [flag de harness como mecanismo de invocação](flag-de-harness-como-mecanismo.md) | acopla governança a um harness; três de cinco degradariam em silêncio | ADR 0016 |
| [spec dentro da ADR](spec-dentro-da-adr.md) | ciclos de vida opostos: ADR é permanente, spec se esgota | ADR 0017 |
| [pacote de terceiro como skill](pacote-de-terceiro-como-skill.md) | capacidade é a API de um pacote; adotar pacote é decisão de stack, não de acervo | triagem de 2026-10-12 |
| [guarda de comando por substring, sem ressalva de leitura](guarda-de-comando-por-substring-sem-ressalva.md) | recusa a menção junto com a execução, e impede ler as regras que aplica | triagem de 2026-10-12 |

## Como escrever um

Cinco seções, todas obrigatórias. "Condição de reabertura" aceita "nenhuma prevista", mas
**escrita** — omitir transforma recusa circunstancial em dogma.
