<!-- Caminho relativo: docs/recusados/pacote-de-terceiro-como-skill.md -->

# Pacote de terceiro como skill

**O que foi pedido.** Importar uma skill cuja capacidade é a **API de um pacote específico** —
no caso concreto, migrar testes de `as` para `@total-typescript/shoehorn`, com instalação,
busca das ocorrências e substituição pelas três funções do pacote.

**Por que está fora.** Reprova a primeira perna da ADR 0019 por duas vias independentes. Não
há falha observada no formato `rodei`/`obtive`/`esperava`, e não há lacuna demonstrada: a
capacidade não é "escrever dado de teste parcial", é a interface de um pacote. A primeira
pertence ao acervo e entra como padrão em skill existente; a segunda é **decisão de stack**, e
stack se decide em `definir-stack`, com o projeto na mesa. Uma skill de acervo que recomenda
pacote faz a escolha pelo projeto que ainda não existe.

Há um segundo custo, que não é de orçamento: skill assim envelhece com a versão do pacote, e
quem a lê não tem como saber se envelheceu.

**Condição de reabertura.** Evidência no formato da ADR 0019 vinda de projeto real nosso — o
`as` num teste passando verde depois de o tipo mudar, com o comando e o resultado. Aí a decisão
é sobre aquele projeto e aquele pacote, com ticket próprio, e o padrão já escrito em
`teste-primeiro` (MT-47) diz o que o pacote tem de ganhar da fábrica de dados na linguagem.

**Pedidos anteriores.** 2026-10-12, na triagem de biblioteca de terceiros.

**Decidido em.** Triagem de 2026-10-12, item `migrate-to-shoehorn`. Padrão aproveitado no
MT-47.
