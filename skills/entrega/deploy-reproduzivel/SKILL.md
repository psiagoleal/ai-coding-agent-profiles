---
name: deploy-reproduzivel
description: >-
  Empacotamento e entrega em que o rollback é escrito antes do deploy e o
  sucesso é confirmado por sinal externo: imagem com versão fixada e sem
  segredo, configuração por ambiente, migração de banco como passo próprio e
  registro do que foi para produção. Aciona ao criar Dockerfile ou compose, ao
  preparar ou executar deploy, ao mexer em migração que vai para produção, e
  quando alguém pergunta "como se volta atrás?".
---

# deploy-reproduzivel — o rollback se escreve antes, não durante

Durante um incidente ninguém projeta o caminho de volta: repete comando, tenta o que lembra e
piora. O rollback tem de existir **por escrito, antes**, quando ainda há calma e ninguém está
com o telefone tocando.

## As duas leis

> **1. Sem rollback escrito, não há deploy.** Uma linha basta — mas ela existe antes de subir.
>
> **2. Deploy é confirmado por sinal externo.** Consulte o alvo e leia a resposta. "O comando
> saiu sem erro" não é confirmação (`critico-independente`).

## A imagem

- **Versão fixada em tudo**: base (`python:3.13-slim`, não `latest`), gerenciador e
  dependências pelo *lockfile*. `latest` faz a imagem de hoje ser diferente da de ontem sem
  que nada no repositório tenha mudado.
- **Multi-estágio**: compilar num estágio, copiar o artefato para um final enxuto. O
  compilador não vai para produção.
- **Usuário sem privilégio** (`USER app`), sistema de arquivos só de leitura quando der.
- **Nenhum segredo na imagem** — nem em `ARG`, nem em `ENV`, nem num arquivo apagado depois:
  **a camada anterior fica**, e quem tem a imagem tem o segredo (`secrets-guard`).
- **`.dockerignore` antes do primeiro `build`**: sem ele vão `.git`, `.env`, `node_modules` e
  dados para dentro do contexto — lento e perigoso.
- **`HEALTHCHECK` que consulta a dependência**, não o processo.

## Configuração e segredo

Configuração vem do ambiente; segredo vem do cofre, **em tempo de execução**. O `.env` é de
desenvolvimento, fica no `.gitignore` e no `.claudeignore`, e tem um `.env.example` sem valor
real ao lado. Variável faltando derruba o serviço no arranque, de propósito: subir com
configuração de desenvolvimento em produção é pior que não subir.

## Compose: desenvolvimento, e diga quando não for

`compose.yaml` resolve ambiente local com banco e dependências. Se ele também roda em
produção, **escreva isso** e trate a diferença explicitamente — reinício, limites de recurso,
volume, rede. Compose de desenvolvimento promovido a produção em silêncio é a origem do "na
minha máquina funciona" invertido: funciona lá e ninguém sabe por quê.

## Migração de banco é passo próprio

- **Nunca no arranque do aplicativo.** Duas réplicas subindo ao mesmo tempo migram em paralelo.
- **Compatível para frente**: primeiro a mudança que aceita os dois formatos, depois a que
  remove o antigo. Assim o rollback do código não exige rollback do banco.
- **Migração destrutiva** (remover coluna, tabela) só depois que nenhum código em produção a
  usa — e com cópia de segurança verificada, não presumida.

## O procedimento, escrito antes

Use `templates/PROCEDIMENTO-DEPLOY.template.md`. Ele obriga cinco respostas:

1. **O que sobe** — versão e *commit*, não "a última".
2. **Pré-condições** — CI verde na mesma revisão, migração revisada, janela combinada.
3. **Passos** — comandos exatos, na ordem.
4. **Verificação** — o comando que consulta o alvo e o que se espera ver: versão respondida
   pelo serviço, `/health` checando dependência, erro por minuto estável.
5. **Rollback** — o comando de volta, quanto tempo leva, o que ele **não** desfaz (dado
   migrado, mensagem enviada, e-mail disparado).

A quinta pergunta é a que mais ensina: descobrir na hora que o rollback não desfaz a migração
é o pior momento possível.

## Depois de subir

- **Janela de observação** declarada — 15 minutos, uma hora, o que o risco pedir. Deploy não
  termina no comando; termina na observação.
- **Registro**: o que subiu, quando, quem autorizou e o resultado da verificação. É o que
  responde "desde quando isto está quebrado?" sem arqueologia.
- **Reverteu?** Registre o motivo e abra ticket (`micro-ticket-planner`). Rollback sem ticket
  vira o mesmo deploy repetido na semana seguinte.

## O que você vai pensar para pular o procedimento

| O que você vai pensar | Por que não vale |
|---|---|
| "É uma mudança pequena" | O tamanho da mudança não tem relação com o tamanho do estrago. |
| "Se der errado eu volto o commit" | Voltar o código não volta o banco, nem a mensagem já enviada. |
| "Subiu sem erro, está no ar" | Sem consultar o alvo, você sabe que o comando terminou — não que o serviço responde. |
| "Depois eu escrevo o procedimento" | Depois é durante o incidente, que é exatamente quando não se escreve nada. |
| "Uso `latest` para pegar correção de segurança" | E também pega mudança incompatível sem aviso. Fixe e atualize por decisão. |

## Ligação com o resto do acervo

`pipeline-como-gate` produz o artefato que sobe · `criar-servico-fastapi` dá o `/health` que a
verificação consulta · `secrets-guard` para o segredo em tempo de execução ·
`gates-de-conclusao` para o critério de aceite do deploy · `adr-writer` para a decisão de
plataforma · `atribuicao-de-falha` quando o mesmo deploy falha duas vezes.

## Definição de pronto da skill

- [ ] Existe procedimento escrito **antes** do deploy, com as cinco respostas.
- [ ] O rollback está escrito, com tempo estimado e o que ele **não** desfaz.
- [ ] Imagem com versões fixadas, multi-estágio, usuário sem privilégio e sem segredo em
      nenhuma camada.
- [ ] `.dockerignore` existe e cobre `.git`, `.env` e dados.
- [ ] Configuração vem do ambiente; falta de variável derruba o arranque.
- [ ] Migração é passo próprio, compatível para frente, e não roda no arranque do aplicativo.
- [ ] A verificação pós-deploy consultou o alvo — versão respondida e `/health` checando
      dependência — e a saída foi lida.
- [ ] Janela de observação declarada e cumprida; o que subiu foi registrado.
