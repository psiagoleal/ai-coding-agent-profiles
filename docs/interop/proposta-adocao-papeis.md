<!-- Caminho relativo: docs/interop/proposta-adocao-papeis.md -->

# Proposta de ADR de adoção — subagente por papel nomeado

> **O que é este documento.** Um rascunho de ADR **para o outro repositório**, mais a
> contraparte que cabe a este. A ADR de não-adoção de lá diz que a adoção exige uma ADR
> própria; esta é a proposta dela, escrita na filosofia que as motivações técnicas já
> indicaram — não uma que as contorne.
>
> Numeração e redação final são de lá. Aqui vai o conteúdo e o que nos toca entregar.
> Data: 2026-09-29

## O princípio que a não-adoção já estabeleceu

As três objeções da avaliação não são contra papéis nomeados; são contra **papel que decide o
que não lhe cabe**. Lidas juntas, elas dão a regra:

> **O papel diz o que o subagente é. Nunca diz onde ele roda, nem o que ele pode.**

Rota é do roteador; permissão é da política. O papel contribui com a terceira coisa, que hoje
se repete à mão a cada delegação: instruções, recorte de atenção e critério de saída.

Disso decorre tudo o mais, inclusive o que a adoção **não** pode fazer.

## O que a ADR de adoção decidiria

**1. O papel é contexto, não configuração.** O que se adota é `name`, `description` e o
**corpo** de instruções. O que se ignora — explicitamente, com erro, nunca em silêncio — é
qualquer campo que pretenda decidir rota ou ampliar permissão.

**2. Nível de raciocínio → task-class, por tabela declarada.** O frontmatter canônico traz
`model:` (`opus`/`sonnet`/`haiku`), e o gerador **já traduz para nível** (`high`/`medium`/
`low`), sem jamais emitir nome de modelo. A adoção precisa de uma linha de configuração que
mapeie **nível → task-class**, por exemplo:

```toml
[subagentRoles.levelToTaskClass]
high = "revisao-profunda"
medium = "chat"
low = "rapida"
```

Nível ausente herda a task-class da sessão-mãe. Nível que não esteja na tabela é **erro de
carga**, não o padrão — porque "cair no padrão" é como um papel caro silenciosamente vira
barato, e ninguém percebe.

**3. `tools:` só restringe.** O conjunto efetivo é a **interseção** com a política de
permissão de subagente. Pedido que amplie é **erro ao carregar**, com o nome do papel e a
ferramenta em excesso — nunca precedência silenciosa. Assim a política continua fonte única
de verdade, e o papel expressa apenas "preciso de menos que isto".

**4. Egresso não se toca.** O papel não tem campo de egresso e não pode ganhar um. A classe
continua vindo do teto da sessão-mãe, com o invariante intacto: subagente iguala ou restringe,
nunca amplia.

**5. Corpo que pressupõe outro harness é recusado, não improvisado.** Metade das unidades do
acervo tem dependência de um harness específico — *slash command*, ferramenta própria, formato
de saída. Carregar um papel cujo corpo pede o que não existe produz subagente que falha no meio
do trabalho, e o custo cai em quem pediu.

A adoção exige, então, que **o papel declare as suas dependências** e que o carregador recuse
o que não pode cumprir, listando o motivo. Isso é entrega **nossa** — ver a seção seguinte.

**6. Descoberta e precedência seguem a regra que já existe** entre os diretórios de adaptador,
inclusive o aviso sobre o que ficou de fora.

**7. A trilha registra o papel.** Cada despacho com papel grava identificador do papel,
task-class resolvida e classe de egresso — **identificador e classe, nunca conteúdo**, como a
ADR da trilha fixou. Sem isso, não há como medir se papel melhora resultado, e a adoção vira
questão de gosto.

## Critério de aceite da adoção

A ADR só se considera cumprida quando, no CI de lá:

- um papel que pede ferramenta além da política **falha ao carregar**, com mensagem que nomeia
  o papel e a ferramenta;
- um papel com nível fora da tabela **falha ao carregar**;
- um papel com dependência de harness não disponível **é recusado**, e o motivo aparece;
- um papel válido carrega, roda e aparece na trilha com papel, task-class e classe de egresso;
- nenhum caminho de código lê provedor, modelo ou classe de egresso de arquivo de papel.

Os quatro primeiros são testes de **recusa**. Adoção que só prova o caminho feliz repete o
problema que a não-adoção evitou: suporte parcial que parece completo.

## A contraparte deste repositório

Nada disso é possível sem que o acervo diga o que cada papel exige. Três entregas nossas:

**a) Declarar dependência de harness no frontmatter.** Um campo novo, preenchido a partir da
medição que já fizemos, com três valores possíveis: `nenhuma` (o corpo só usa as seis
ferramentas mapeadas), `<harness>` (usa recurso específico) ou `desconhecida` (ainda não
auditado). O carregador de lá recusa o que não puder cumprir — e `desconhecida` é recusa
também, até alguém olhar.

**b) Um verificador**, para que isso não dependa de vigilância: confere que todo papel declara
nível e dependência, que `tools` só usa nomes do conjunto mapeado, e que nenhum papel traz
nome de modelo ou de provedor. Entra no nosso CI, junto dos outros autotestes.

**c) Manter a tradução de nível**, que já existe e fechou a primeira trava: o gerador nunca
emite nome de modelo.

## O que esta proposta **não** pede

- Não pede que o outro projeto leia os nossos arquivos por caminho fixo, nem que o nosso
  framework vire dependência dele. O acoplamento continua sendo formato, não instalação.
- Não pede campo de egresso, de provedor ou de modelo no papel.
- Não pede adoção de todos os 44 papéis: adotar o mecanismo e recusar papel incompatível é
  melhor do que adaptar o acervo inteiro para caber.

## Por que propor agora, e não depois

A não-adoção registrou que o trabalho real é decidir **duas** coisas: o mapeamento de nível
para task-class e a convivência entre `tools:` e a política. A primeira encolheu quando o
gerador passou a emitir nível. Esta proposta fecha a segunda com a regra mais simples possível
— **interseção, e divergência é erro** —, que não cria fonte de verdade nova.

Se a proposta for recusada, o custo foi o de escrever um documento; a não-adoção continua
válida e agora com uma alternativa avaliada por escrito, que era o propósito declarado dela.
