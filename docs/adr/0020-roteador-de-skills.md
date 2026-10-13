<!-- Caminho relativo: docs/adr/0020-roteador-de-skills.md -->

# ADR 0020: Roteador de skills, com sincronia verificada por comando

- **Status:** Accepted — construção condicionada, ver §3
- **Data:** 2026-10-11
- **Decisores:** Iago Leal (mantenedor), com Claude Code
- **Tags:** skills, descoberta, catálogo

## Contexto

A descoberta hoje é varrer o catálogo inteiro. Com o catálogo estourando o orçamento em uso
real, isso significa que o modelo paga por todas as skills para encontrar uma — e, quando o
teto foi atingido, a descoberta degradou **em silêncio**, com dezesseis skills sumindo do
catálogo sem aviso.

Roteador é camada de compressão: troca o varrimento por um artefato pequeno que mapeia
**situação → skill**. Não é redundante com o catálogo, porque responde pergunta diferente —
seleção, não existência.

## Decisão

> Adotar um roteador, **com verificador de sincronia como comando**, nunca como regra escrita.

### 1. O artefato

Mapeia situação para skill, em linguagem de quem tem o problema, não em nome de skill.

### 2. O verificador

`scripts/checar-roteador.py` reprova quando:

- existe skill alcançável que o roteador não menciona;
- existe entrada no roteador para skill que não existe mais.

A regra de re-sincronização da biblioteca analisada é prosa, e é o único trecho dela que **não
deve ser copiado**: prosa sem comando é precisamente o defeito que a nossa própria doutrina
condena, e que já nos custou uma skill de 217 linhas sem script.

A justificativa da disciplina, essa sim importada: **um roteador desatualizado é pior que
nenhum, porque roteia errado com autoridade.**

### 3. Construção condicionada

O roteador é **aceito agora e construído depois da triagem** das skills de terceiros. O mapa
só estabiliza quando o catálogo parar de mudar; escrever antes é reescrever depois. Ao fim da
triagem, a decisão é **reverificada** antes da construção — se o catálogo final não justificar,
esta ADR é revista por uma nova, não ignorada.

## Consequências

**Positivas.** Descoberta deixa de custar o catálogo inteiro. O verificador transforma em
falha o que hoje é deriva silenciosa.

**Negativas.** Artefato permanente a mais, que pesa no contexto — e o roteador é ele próprio
uma skill, sujeita ao mesmo orçamento que pretende aliviar. O ganho líquido depende de ele ser
curto, e isso é restrição de projeto, não detalhe.

**Risco registrado.** Roteador mal mantido é pior que ausência. O verificador existe por isso,
e é pré-requisito da construção, não complemento dela.
