<!-- Caminho relativo: docs/adr/0022-selecao-do-acervo-na-instalacao.md -->

# ADR 0022: Seleção do acervo na instalação, derivada do projeto

- **Status:** Accepted
- **Data:** 2026-10-11
- **Decisores:** Iago Leal (mantenedor), com Claude Code
- **Tags:** skills, catálogo, instalador, acervo

## Contexto

O acervo tem **169 skills e 83,2 KB de descrição de catálogo** (ADR 0016, medição de
2026-10-11). Um harness já cortou um catálogo de 55,3 KB contra teto de 50 KB, em silêncio
para o modelo. Instalar o acervo inteiro em um projeto é 1,66× esse teto e nunca foi a
intenção de ninguém.

A alavanca estrutural, então, não é reduzir o acervo — é **escolher o que dele entra em cada
projeto**. Um projeto de serviço em Python não tem o que fazer com skills de interface, de
aprendizado de máquina ou de domínio elétrico, e o custo de carregá-las não é só orçamento: é
ruído na decisão do modelo sobre qual skill se aplica.

Isso já foi feito à mão, uma vez, numa adaptação real: escolheu-se por tipo de projeto e por
stack, item a item, e funcionou. O que não existe é a derivação automática.

### O que o instalador já faz

Medido no `scripts/setup-profile.sh`, a infraestrutura está pronta e a lacuna é estreita:

| Peça | Situação |
|---|---|
| Múltiplas fontes de acervo (público + privado) | **existe** — `FONTES_EXTRAS` / `LIBS` |
| Nome único em todo o acervo, verificado | **existe** — reprova skill em duas fontes |
| Seleção explícita por lista | **existe** — `--skills` |
| Expansão de categoria (`categoria/*`) e de `@padrao` | **existe** |
| Padrão quando nada é pedido | **existe** — só o núcleo de governança |
| Verificação de dependência entre skills selecionadas | **existe** — nomeia a que falta |
| **Derivar a lista do projeto** | **não existe** — é o objeto desta ADR |

Portanto não se constrói mecanismo novo de instalação. Constrói-se o que **produz a lista** que
o mecanismo já consome.

## Decisão

> A instalação **deriva** a seleção de skills do projeto de destino — tipo, stack e requisitos
> — e grava a seleção resultante no projeto, como entrada versionada e auditável. O acervo
> inteiro nunca é instalado por padrão.

### 1. Três sinais, em precedência declarada

1. **Manifesto do projeto**, se existir: vence tudo. É a decisão humana já tomada.
2. **Detecção da árvore**: `Cargo.toml`, `pyproject.toml`, `package.json`, `CMakeLists.txt`,
   `*.tf`, `Dockerfile` e afins mapeiam para categorias do acervo.
3. **Pergunta ao mantenedor**, quando a detecção for ambígua ou vazia — e não silêncio com
   padrão escolhido por omissão, que é o modo de falha que a ADR 0016 combate.

### 2. A seleção derivada é gravada, não implícita

A instalação escreve no projeto o conjunto escolhido e **por qual sinal** cada item entrou.
Sem isso não há como responder "por que esta skill está aqui?" seis meses depois, nem repetir
a instalação com o mesmo resultado.

### 3. O que nunca é derivado

O núcleo de governança entra sempre, independente de stack: é o que define como se trabalha,
não o que se constrói. Derivação atua sobre o resto.

### 4. Não fecha o orçamento sozinha — mede

A seleção precisa **relatar o tamanho de catálogo resultante** ao fim da instalação. É a única
forma de o orçamento deixar de ser descoberto em campo, por aviso de um harness, meses depois.

## Decisões em aberto

Esta ADR não é implementável como está. Falta decidir, e está registrado aqui para que a
lacuna não passe por consenso:

1. **O formato e o lugar do manifesto** — arquivo próprio no projeto, ou seção em arquivo que
   já existe.
2. **A granularidade do mapa stack → acervo** — por categoria de diretório, que já existe e
   custa pouco, ou por marcação dentro de cada `SKILL.md`, que é mais fina e mais caro de
   manter.
3. **O que acontece na reinstalação** quando a árvore mudou de stack: re-derivar e remover o
   que saiu, ou só acrescentar.

## Consequências

**Positivas.** O orçamento de catálogo passa a ser consequência de uma decisão registrada. O
acervo pode crescer sem que o crescimento vire custo em todo projeto — o que preserva o motivo
de olhar acervos de terceiros: aumentar o nosso. A seleção manual que funcionou uma vez deixa
de depender de quem lembra como foi feita.

**Negativas.** Mapa de stack para categoria é manutenção recorrente, e erra nos projetos
híbridos. Detecção por arquivo-marcador é heurística: `package.json` não distingue serviço de
interface. Por isso a pergunta ao mantenedor é parte da decisão, e não um atalho.

**Relação com outros itens.** É a alavanca 1 da ADR 0016, e é quem fecha o orçamento que
aquela não fecha. Depende da medição de corte por harness (MT-44) para saber contra qual teto
relatar. Implementada pelo MT-43.
