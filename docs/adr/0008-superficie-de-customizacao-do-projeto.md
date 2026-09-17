<!-- Caminho relativo: docs/adr/0008-superficie-de-customizacao-do-projeto.md -->

# ADR 0008: Superfície de customização do projeto e separação governança/domínio nas skills

- **Status:** Accepted
- **Data:** 2026-08-12
- **Decisores:** Iago Leal (mantenedor)
- **Tags:** setup-profile, update, ilhas-user, skills, catálogo, preservação

## Contexto

Uma varredura das 21 pastas `~/dev/*/skills` mostrou que a biblioteca deste repositório já é
a versão mais recente de todas as skills compartilhadas — nada precisava ser retroportado.
O que a varredura revelou foi outra coisa: **como os projetos vinham contornando os limites
do `--update`**.

Três evidências:

1. **Ilhas inventadas pelos projetos.** O template oferecia apenas `comandos-exatos` e
   `estrutura-diretorios`. Mesmo assim, `clima_db`, `LT-Ampacidade` e `LT-HIW` criaram por
   conta própria `ambiente-desenvolvimento` e `estilo-codificacao`; `ai_basics` criou
   `modo-pesquisa` (um regime inteiro de operação para trilha de pesquisa) e `agentry` criou
   `interop` (o contrato com o projeto irmão). Todas seriam rebaixadas a `USER:ORPHAN` e
   realocadas para o fim do arquivo no primeiro `--update` — preservadas, mas desmontando a
   estrutura do documento. A demanda por pontos de customização existia; faltava oferecê-los.

2. **Risco de perda de dados no perfil pessoal.** `README.md`, `CHANGELOG.md` e `LICENSE`
   caíam no balde `rule` e seriam **sobrescritos** pelo template. `agentry`, `atldp`,
   `docling_service` e `claude-telegram-bridge` têm READMEs reais e extensos; um `--update`
   os teria destruído. O bug nunca se manifestou apenas porque `--update` ainda não havia
   sido rodado nesses repositórios.

3. **Skills de domínio sem lugar.** `~/dev/general/skills` acumulou `mockup-lab`
   (prototipagem de UI com Penpot) e `pc-builder` (preço e compatibilidade de hardware).
   Úteis, mas presas a uma tecnologia — o oposto do critério declarado da biblioteca
   ("governança/fluxo, independentes de setor"). Sem categoria, ou ficavam fora do controle
   de versão ou entrariam por padrão em projetos de linha de transmissão.

## Decisão

### 1. Novo balde `scaffold` (andaime)

`README.md`, `CHANGELOG.md`, `LICENSE` **da raiz** e `docs/adr/README.md` passam a ser
andaimes: entregues na instalação como ponto de partida, **nunca sobrescritos** no
`--update`. A autoria passa ao projeto no instante em que ele os edita.

`docs/adr/README.md` só entrou nesta lista depois de a primeira execução da migração
apagá-lo: o índice de ADRs do `LT-Ampacidade`, com 15 entradas, virou a linha-exemplo do
template. O índice cresce a cada ADR registrado — é do projeto, não do framework. O README
da biblioteca de skills segue sendo regenerado, mas como híbrido com ilha.

### 2. Ilhas oficiais ampliadas

Os três perfis passam a oferecer `ambiente-desenvolvimento` (§1), `estilo-codificacao` (§4),
`confidencialidade-projeto` (fim da §0) e uma seção **§10 "Seções específicas do projeto"**
com a ilha `secoes-adicionais`, destinada a seções inteiras que só existem naquele
repositório. Os dois primeiros IDs foram escolhidos para casar exatamente com os que
`clima_db`, `LT-Ampacidade` e `LT-HIW` já haviam inventado — a promoção é retroativa: o que
seria órfão vira ilha reconhecida, no lugar certo do documento.

`confidencialidade-projeto` responde ao caso do `neocad`: um repositório público cujo
mantenedor também toca projetos sob NDA, e que precisou escrever uma §0.1 inteira definindo
a fronteira (o que jamais pode atravessar, origem permitida de *fixtures*, como reportar um
achado obtido contra material confidencial). Postura de confidencialidade é justamente o
tipo de regra que o perfil define em geral e o projeto precisa apertar em particular.

O perfil `pessoal` **não** recebeu `estrutura-diretorios`: ele não tem seção de mapa de
diretórios e nenhum dos cinco projetos sob esse perfil demandou uma. Criá-la renumeraria as
seções 3–10 sem evidência de necessidade; quem quiser um mapa usa a §10.

**Dois modos de ilha.** A migração mostrou que islar a seção inteira nem sempre serve. Em
§1/§2/§3/§4 o projeto **substitui** o template (ambiente, stack, comandos, estilo são dele),
mas em §6/§7/§8/§9 ele **acrescenta** a uma política que deve continuar viva: `clima_db`
somou o cofre `~/cred/credentials.json` ao §7 sem querer congelar o resto das regras de
segredo. Daí `adendos-fronteiras`, `adendos-seguranca`, `adendos-fluxo` e `adendos-skills`,
posicionadas ao **final** da seção: a política é regenerada, o acréscimo é preservado. Sem
essa distinção, cada ilha nova congelaria mais regramento — o custo citado nas consequências.

### 2b. Migração: promover ilha exige semear o alvo

Promover uma seção a ilha **não basta**. No `--update`, o conteúdo da ilha vem do *alvo*; se
o alvo não tem a ilha, o template vence e a customização do projeto é apagada. A primeira
execução desta migração perdeu exatamente assim o ambiente de 10 projetos (`WSL2 com Ubuntu
24`, `IDE: VSCode`), o `Svelte 4` de três, a proibição de mexer em `legacy/` do
`clima-downscaling` e os *Conventional Commits* do `torre-optim` — tudo recuperado do
backup.

Portanto: **toda promoção de seção a ilha exige um passo de semeadura** que insira os
marcadores no alvo em volta do conteúdo que ele já tem, antes do primeiro `--update`. Para
ilhas de adendo, a semeadura é a diferença de linhas entre a seção do alvo e a do template
anterior. Sem esse passo, `--update` é destrutivo justamente para quem mais customizou.

### 3. `skills/README.md` vira híbrido, com catálogo local

O README da biblioteca deixa de ser `rule` e passa a `hybrid_text`, com a ilha
`catalogo-local`. Um projeto que crie skills próprias registra-as ali e a entrada sobrevive
ao `--update`. As skills em si nunca correram risco — o script só escreve as que instala —
mas o catálogo que as tornava descobríveis era sobrescrito.

Isso exigiu qualificar o caminho relativo passado ao classificador: o README da biblioteca
era anunciado como `"README.md"` puro, o que agora colidiria com o andaime do projeto.

### 3b. `USER:RESCUE` em arquivos linha-a-linha

Em `.claudeignore` e `.env.example`, uma linha editada **fora** de ilha passa a ser
reanexada num bloco `USER:RESCUE` com aviso, em vez de sumir. O `clima_db` tinha `secrets/`
e `**/target/` fora da ilha do `.claudeignore`; a regeneração os apagou silenciosamente na
primeira execução. Ali cada linha é um controle — uma pasta que sai do ignore volta a ser
indexada pelo agente, e o efeito de perdê-la não aparece em nenhum teste.

### 4. Marcador só vale em início de linha

O reconhecimento de `USER:BEGIN`/`USER:END` passa a exigir que a linha **comece** com o
comentário (`<!--` ou `#`). Sem isso, documentar o mecanismo dentro do próprio `AGENTS.md`
— exatamente o que a §10 faz — desbalancearia o parser e abortaria a atualização do arquivo.

### 5. Categoria de domínio nas skills

A biblioteca passa a ter dois níveis: **governança** na raiz (instalada por padrão) e
**domínio** em subpasta de categoria (`dominio/`), que exige `--skills dominio/<nome>`
explícito. A descoberta automática só varre a raiz, então uma skill de domínio jamais entra
sem pedido. O adaptador `.claude/skills/` permanece **plano** (o Claude Code descobre skills
em um nível só): o link usa o *basename*, apontando para o caminho aninhado na pasta neutra.

Artefatos de ambiente (`node_modules/`, `.venv/`, `__pycache__/`, `*.pyc`) nunca são
instalados — `mockup-lab` carregava 18 MB de Playwright. Dado do usuário sai de dentro das
skills: `pc-builder` ganhou `--lista` para apontar o `build.json` a um diretório de trabalho
do projeto, com um fixture sintético em `examples/`.

## Consequências

**Positivas.** O `--update` deixa de ser uma operação que exige coragem: os quatro baldes
cobrem todos os arquivos que os projetos de fato editam. As customizações que os projetos
inventaram passam a ser suportadas no lugar onde já estavam, sem realocação. A biblioteca
pode crescer com skills de domínio sem poluir projetos que não as querem.

**Negativas.** Conteúdo dentro de uma ilha **para de receber atualizações do framework** —
é o preço da preservação, e cresce a cada ilha nova. `estilo-codificacao` é o caso mais
sensível: era regra do framework e passa a ser território do projeto. Mitigação: manter nas
ilhas o que é específico e fora delas o que é política, e revisar periodicamente se uma ilha
muito replicada não deveria voltar a ser regra.

**Migração (executada em 2026-08-12, 20 projetos).** `skills/README.md` foi substituído pelo
novo template antes do primeiro `--update` — nunca foi editável pelo usuário (era `rule`), e
gerar um `.new` inútil em 20 repos não ajudaria. `btc_market` e `neocad` tinham `AGENTS.md`
legado sem nenhuma ilha; `docling_service`, `neocad`, `LT-Ampacidade` e `btc_market` tinham
`.env.example`/`.claudeignore` na mesma situação — todos receberam marcadores em volta do
conteúdo existente. As ilhas de id desconhecido (`interop` no `agentry`, `modo-pesquisa` no
`ai_basics`) foram reancoradas em `secoes-adicionais` em vez de virarem `USER:ORPHAN` no fim
do arquivo.

A verificação foi feita por diferença de linhas contra um backup pré-migração, descontando o
texto do template anterior — o único jeito de distinguir "o framework mudou esta linha" de
"apagamos conteúdo do projeto". Ao final restaram 11 linhas de divergência, todas benignas
(requebra de linha do texto do framework, renumeração de cabeçalho e a §9 antiga substituída
pela lista ampliada de skills). O `--update` foi confirmado idempotente nos 20 alvos.

## Diretriz de Conformidade

Ao acrescentar um arquivo ao perfil, classifique-o explicitamente em `bucket_for` antes do
primeiro `--update` que o alcance. O padrão é `rule` (sobrescrever) — seguro para ponteiro e
regramento, destrutivo para qualquer coisa que o projeto vá editar. Na dúvida entre `rule` e
`scaffold`, pergunte quem é o autor do arquivo depois de seis meses de uso.
