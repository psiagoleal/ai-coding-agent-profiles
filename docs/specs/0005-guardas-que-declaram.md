<!-- Caminho relativo: docs/specs/0005-guardas-que-declaram.md -->

# Spec 0005 — Guardas e verificadores que declaram o que não examinaram

- **Status:** Rascunho — sem decisão pendente; criticada em contexto limpo em 2026-10-29,
  achados incorporados; aguarda aceite do mantenedor
- **Data:** 2026-10-29
- **Decide a partir de:** ADR 0023 §3 (contenção no git primeiro); ADR 0017 e ADR 0024
  (verificação da cadeia spec ↔ ticket); parentesco registrado no MT-41
- **Tickets:** [MT-24](../tickets/MT-24.md) (guarda de git, camada 1) ·
  [MT-40](../tickets/MT-40.md) (guarda de vazamento: nome de ref e caminho) ·
  [MT-41](../tickets/MT-41.md) (painel: seção desconhecida) · [MT-48](../tickets/MT-48.md)
  (links: o que o `.gitignore` ignora) · [MT-59](../tickets/MT-59.md) (cadeia spec ↔ ticket)

## Problema

O mesmo defeito apareceu quatro vezes, em quatro ferramentas diferentes. Cada uma responde só
à pergunta que sabe fazer, e o seu "válido", "limpo" ou silêncio é lido como "nada errado":

| Ferramenta | Disse | Não tinha examinado |
|---|---|---|
| guarda de git | liberado | indireção que apaga o texto do comando (`g=push; git $g`) |
| guarda de vazamento | `limpo` | nome de branch publicado com termo confidencial |
| verificador do painel | `painel válido` | linha sob seção de título inventado |
| verificador de links | 254 arquivos, 6 problemas | que os seis estavam em pasta ignorada pelo git |

A guarda de vazamento já foi lida como "limpo" enquanto um nome de branch publicado
carregava termo declarado (2026-10-09). O defeito já custou um vazamento.

## Solução

Um contrato comum para toda guarda e todo verificador do framework, e a correção de cada um
dos quatro pontos cegos medidos:

1. **Autoteste no CI**, com caso fabricado para cada classe que a ferramenta diz cobrir.
2. **Declaração do que não foi examinado**, impressa no fim de toda execução, inclusive a que
   passa.
3. **Ausência de insumo é erro**, nunca "nada a fazer" (como a guarda de vazamento já faz com
   a lista ausente).

**As ferramentas cobertas**, lista fechada: `checar-comando-git.sh` e o hook do git que o
MT-24 cria; `checar-vazamento.py` (fonte privada); `checar-painel.py`; `checar-links.py`;
`checar-cadeia.py` (MT-59); `checar-mensagem-commit.sh`. Ferramenta nova de verificação entra
na lista pela própria spec que a criar.

## Histórias

1. **Como mantenedor**, quero que "limpo" venha com o que não foi olhado, para não ler
   cobertura onde não há.
2. **Como mantenedor**, quero que o git recuse o commit do agente por qualquer caminho de
   invocação, inclusive quando troco de harness.
3. **Como mantenedor**, quero que o nome de branch, tag e remoto passe pela mesma guarda que o
   conteúdo.
4. **Como mantenedor**, quero que a verificação local dê o mesmo número que o CI.
5. **Como mantenedor**, quero que ticket citando spec inexistente reprove, e que spec sem
   ticket apareça, como a ADR 0017 já pedia.

## Decisões de implementação

| Decisão | Escolha | Onde |
|---|---|---|
| Formato da declaração | última linha `não examinado: <lista>`, também na saída de sucesso | esta spec |
| Guarda de git | hook do próprio git como camada primária, negando por padrão sob marca de sessão de agente; token de escape prefixado por invocação, digitado pela pessoa | MT-24 |
| Escape | `deny` no harness para o token, `--no-verify` e `core.hooksPath` | MT-24, camada 2 |
| Marca de sessão por harness | a camada 1 conhece a de cada agente do manifesto; a lista entra na matriz de lacunas | MT-24, spec 0002 |
| Vazamento em superfície | nome de ref e caminho de arquivo contam como texto, inclusive o não versionado sob o clone | MT-40 |
| Links e `.gitignore` | `git check-ignore --stdin` em lote; fora de repositório, comportamento atual declarado na saída | MT-48 |
| Painel | conjunto fechado de quatro seções — `Em aberto`, `Concluídos`, `Abandonados`, `Recusados` —; título fora dele reprova | MT-41 |
| Sessão sem marca de agente | o hook não tem como distinguir de pessoa e libera; harness sem marca conhecida é lacuna na matriz da spec 0002 | MT-24 |
| Vazamento em ref | refs que moram no clone: branches locais, de rastreamento, tags e nomes de remoto | MT-40 |

## Critérios de aceite

| # | Critério | Prova | Ticket |
|---|---|---|---|
| 1 | Cada ferramenta da lista fechada DEVE ter `--autoteste` com pelo menos um caso fabricado por classe que o cabeçalho de uso dela diz cobrir, e o autoteste DEVE estar no CI | passos do `ci.yml`, um por ferramenta; o revisor confere classe do cabeçalho × caso do autoteste | todos |
| 2 | Toda execução dessas ferramentas, inclusive a que passa, DEVE terminar com a linha `não examinado:` | teste de saída em cada autoteste | todos |
| 2a | SE o insumo declarado de uma ferramenta falta (lista de termos, painel, diretório alvo), ENTÃO ela DEVE sair com código de uso nomeando o insumo, e NÃO DEVE dizer que passou | caso de insumo ausente em cada autoteste | todos |
| 3 | ENQUANTO a sessão tem marca de agente, o hook do git DEVE recusar `commit` e `push` por qualquer caminho de invocação do binário, inclusive `g=push; git $g`, `G=git; $G push`, `bash ./deploy.sh` e `git pu"sh"`. O `--no-verify`, que pula hook, é fechado pelo critério 4 | os quatro casos saem da lista de lacunas do autoteste | MT-24 |
| 4 | QUANDO a pessoa usa o token de escape, o git DEVE aceitar; SE o agente tenta o token, `--no-verify` ou `core.hooksPath`, ENTÃO o harness DEVE recusar | teste da camada 2 | MT-24 |
| 5 | O autoteste da camada de texto DEVE continuar em 25 recusas e 21 liberações | `checar-comando-git.sh --autoteste` | MT-24 |
| 6 | QUANDO um nome de branch, tag ou remoto, ou um caminho sob o clone, contém termo declarado, a guarda de vazamento DEVE sair com 1 nomeando a ref ou o caminho | autoteste com termo fabricado | MT-40 |
| 7 | QUANDO uma linha do painel está sob título fora das quatro seções, o verificador DEVE sair com 1 nomeando o título e a linha | `checar-painel.py --autoteste` | MT-41 |
| 8 | ENQUANTO existir worktree sob `.claude/worktrees/`, o verificador de links com as flags do CI DEVE contar como conferidos só os arquivos não ignorados pelo git — o mesmo número de arquivos e problemas que o CI — e DEVE imprimir à parte quantos pulou por estarem ignorados | autoteste com Markdown quebrado em pasta ignorada: sai 0 e declara 1 pulado | MT-48 |
| 9 | SE um ticket cita spec inexistente, ENTÃO o verificador da cadeia DEVE reprovar; SE uma spec Aceita não tem ticket em aberto nem está Esgotada, ENTÃO ele DEVE listá-la como pendência | `checar-cadeia.py --autoteste`, passo no CI | MT-59 |

## Fora de escopo

- **Garantia completa contra commit do agente.** `--no-verify` pula hook local; fechamento
  real exige `pre-receive` no remoto, que não é deste repositório.
- **Superfícies que moram no servidor**: nome de PR, de issue, commit assinado por terceiro. A
  guarda de vazamento passa a declará-las em `não examinado:`.
- **Traduzir a contenção para outros harness.** [Spec 0002](0002-instalacao-por-agente.md).

## Decisões pendentes

Nenhuma.
