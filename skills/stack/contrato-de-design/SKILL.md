---
name: contrato-de-design
description: >-
  Cria e mantém o docs/DESIGN.md do projeto — o contrato visual de onde o código
  deriva: atmosfera, papéis de cor, tipografia, espaço, receitas por componente
  e anti-padrões, sobre uma arquitetura de tokens em três camadas (primitiva →
  semântica → componente), independente de framework. Aciona ao começar a
  interface de um projeto, quando as cores e espaçamentos começam a divergir
  entre telas, antes de criar o primeiro componente reutilizável, ou quando se
  pede design system, tokens, tema claro/escuro ou padronização de UI.
---

# contrato-de-design — o código deriva do DESIGN.md, nunca o contrário

Sem contrato visual escrito, cada tela recebe a cor que o agente achou razoável naquela
sessão. O resultado não é feio: é **inconsistente**, que é pior — e a correção custa mais que
o trabalho original, porque já está espalhada.

## A regra

> **`docs/DESIGN.md` é a fonte única do visual. Valor que não está nele não entra no código.**
> Mudou a decisão visual, muda o `DESIGN.md` primeiro; o token e o componente vêm depois.

## Arquitetura de tokens — três camadas

Vale em CSS puro, Tailwind, CSS Modules, Qt ou terminal: a ideia é a indireção, não a
sintaxe.

```
1. primitiva   --azul-500: #3b82f6;            escala crua. A interface NUNCA a consome.
2. semântica   --cor-acento: var(--azul-500);  --fundo --texto --borda --superficie. É o que a UI usa.
3. componente  --botao-fundo: var(--cor-acento);  ligação por componente.
```

Três regras de ferro:

- A interface usa **só** a camada semântica ou a de componente. Primitiva direta, nunca.
- **Nenhum valor cru** (hex, `px` de cor de sombra, tamanho de fonte) fora da camada
  primitiva.
- Nomear por **papel**, não por aparência: `--cor-perigo`, não `--vermelho-600`. Nome por
  aparência mente no dia em que o perigo virar laranja.

Trocar de tema é reapontar a camada semântica. Se, para trocar o tema, é preciso mexer em
componente, a indireção não existe de fato.

## O questionário visual

Depois do bloco E de `definir-stack`, e **antes** do primeiro componente. Uma pergunta por
vez; o que a marca ou o produto já define não se pergunta.

1. **Atmosfera** em uma frase: tema claro, escuro ou ambos; denso ou espaçado; sóbrio ou
   expressivo. Esta frase decide metade das outras respostas.
2. **Cor**: acento principal; superfícies (fundo, cartão, elevado); três níveis de texto
   (primário, secundário, desabilitado); estados (sucesso, atenção, erro, informação).
   Para cada uma, o **papel** — onde é usada e onde não é.
3. **Tipografia**: família de texto e de código; os dois ou três pesos que realmente serão
   usados; escala (razão fixa é mais fácil de manter que valores avulsos).
4. **Espaço, raio e elevação**: escala de espaçamento; raio por tipo de componente; como se
   representa elevação — no escuro, luminância funciona melhor que sombra opaca.
5. **Componentes do MVP**: quais existem de fato (botão, campo, cartão, tabela, diálogo) e,
   para cada um, os estados obrigatórios: repouso, foco, desabilitado, carregando, erro,
   vazio. **Vazio e erro são os mais esquecidos** e os que mais aparecem em produção.
6. **Acessibilidade alvo**: contraste mínimo (WCAG AA é o piso), foco sempre visível,
   navegação por teclado.

Resposta que o usuário não tem: proponha **duas** opções concretas e peça a escolha. Pergunta
aberta sobre estética devolve "sei lá, algo bonito".

## O documento

Copie `templates/DESIGN.template.md`. Seções: atmosfera · cores e papéis · tipografia ·
espaço, raio e elevação · receitas por componente (fazer / evitar) · acessibilidade ·
anti-padrões deste projeto. Cada valor aparece **uma vez**, na camada primitiva, com o papel
ao lado.

O documento é curto e opinativo. Catálogo de componente renderizado é outra coisa
(Storybook, página de exemplos) e não substitui o contrato: ele mostra o que existe, não o
que vale.

## Como se verifica que o código segue o contrato

Duas varreduras baratas, boas para gate ou hook:

```bash
# valor cru de cor fora da camada primitiva
grep -rniE '#[0-9a-f]{3,8}\b|rgba?\(' src --include='*.{css,svelte,ts,tsx}' | grep -v tokens
# uso de token primitivo direto na interface
grep -rnE 'var\(--(azul|verde|cinza)-[0-9]+\)' src | grep -v tokens
```

Saída vazia é o esperado. Não vazia, ou o componente está errado, ou o contrato não previu o
caso — e aí o `DESIGN.md` é que precisa mudar.

## Quando não aplicar

Ferramenta interna de uma tela, protótipo descartável, CLI sem interface gráfica. Nesses,
o contrato são três linhas na seção 10 do `AGENTS.md`, e está ótimo.

## O que você vai pensar para pular o contrato

| O que você vai pensar | Por que não vale |
|---|---|
| "É só um projeto pequeno" | O custo aparece na terceira tela, e aí já é retrabalho. |
| "O framework já traz um tema" | Traz valores, não papéis. O tema de terceiro decide por você e muda sem avisar. |
| "Defino os tokens direto no código" | Sem o documento, ninguém sabe **por que** aquele token existe — e o próximo agente inventa outro. |
| "Ajusto a cor só nesta tela" | É exatamente assim que a inconsistência entra, uma exceção por vez. |

## Ligação com o resto do acervo

`definir-stack` pergunta o bloco de interface e manda para cá · `criar-ui-sveltekit` (ou a
skill da stack de UI em uso) **consome** este contrato e não o redefine · `mapa-de-arquitetura`
registra onde os tokens moram · `pr-review-guard` reprova valor cru no diff.

## Definição de pronto da skill

- [ ] `docs/DESIGN.md` existe e foi escrito **antes** do primeiro componente reutilizável.
- [ ] As três camadas de token existem, e a interface não consome a primitiva.
- [ ] Todo token é nomeado por papel, não por aparência.
- [ ] Cada componente do MVP tem receita com os estados repouso, foco, desabilitado,
      carregando, erro e vazio.
- [ ] Contraste alvo declarado e conferido nos pares de cor principais.
- [ ] As duas varreduras de valor cru saem vazias.
- [ ] Mudança visual entrou no `DESIGN.md` no mesmo trabalho que mudou o código.
