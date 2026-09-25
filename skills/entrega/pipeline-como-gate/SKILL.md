---
name: pipeline-como-gate
description: >-
  Pipeline de integração contínua que prova alguma coisa: os mesmos comandos do
  AGENTS.md, na ordem barato→caro, sem passo que não pode falhar, com matriz só
  onde a plataforma muda o resultado, cache que invalida sozinho, segredo fora
  do alcance de fork e permissão mínima. Aciona ao criar ou alterar workflow, ao
  adotar CI num projeto sem pipeline, quando o CI passa e a máquina local falha
  (ou o contrário), e quando um passo vive quebrado e todo mundo aprendeu a
  ignorar.
---

# pipeline-como-gate — CI que não pode reprovar não é gate, é enfeite

O pipeline existe para dizer **não**. Quando ele nunca diz, ninguém percebe: as luzes ficam
verdes, o tempo é gasto e a única coisa provada é que a máquina liga.

## As duas leis

> **1. O gate do CI é o mesmo comando do `AGENTS.md`.**
> Se o CI roda um comando e a ilha `comandos-exatos` diz outro, existem dois contratos — e o
> agente da próxima sessão vai obedecer ao errado.
>
> **2. Todo passo pode reprovar.** `continue-on-error`, `|| true` e teste que não roda
> transformam o gate em decoração.

Confira a primeira por comando:

```bash
python3 skills/entrega/pipeline-como-gate/scripts/checar-gate-ci.py
```

Ele lê os comandos da ilha `comandos-exatos` do `AGENTS.md` e aponta o que o CI **não** roda.

## Ordem: barato antes de caro

O mesmo princípio do `gates-de-conclusao` e do `laco-de-correcao`: cada filtro barato que
reprova poupa uma rodada do caro.

```
formatação e lint (segundos)  →  tipos  →  teste unitário  →  teste de integração
     →  build e artefato (minutos)
```

Quem põe o build primeiro paga cinco minutos para descobrir um espaço a mais.

## Matriz só onde a plataforma muda o resultado

| Projeto | Matriz que se justifica |
|---|---|
| Rust, C++, código nativo, aplicação desktop | Linux, macOS e Windows — o resultado **muda** |
| Python puro, serviço em contêiner | a versão do projeto e a mínima suportada |
| Front web | uma versão de Node; navegador fica para o teste de ponta a ponta |

Formatação e lint rodam **uma vez**, num único sistema: eles não dependem de plataforma, e
triplicar isso só gasta minuto de execução e atrasa o retorno.

### Mas não estreite a matriz por previsão

Medido em campo (2026-09, projeto público em Rust, matriz de três sistemas): a decisão de
arquitetura registrada **previu** que a fragilidade multiplataforma estaria em subir processo
e abrir socket, e autorizava de antemão restringir o teste de ponta a ponta a um só sistema
caso a matriz se mostrasse instável.

**Essa saída nunca foi usada.** Os casos de ponta a ponta passaram nos três sistemas desde a
primeira execução. O que reprovou — **cinco vezes, com cinco causas distintas** — foi outra
coisa a cada rodada: `PATH` sem o binário, resolução de relógio no Windows, separador de
caminho em saída de ferramenta, a isenção das próprias guardas estáticas comparando caminho
como texto, e um `file://` inválido. **Duas eram defeito de produção, não de teste.**

A lição não é "matriz sempre". É que **previsão sobre onde a coisa quebra não sobrevive ao
contato com medição**: estreitar a matriz pelo palpite teria escondido dois defeitos reais — e
teria parecido prudente. Estreite pelo que a execução mostrou instável, com o registro do que
foi observado, nunca pelo que se imagina que vai falhar.

## Cache que invalida sozinho

A chave inclui o *lockfile*: `hashFiles('**/Cargo.lock')`, `hashFiles('**/uv.lock')`,
`hashFiles('**/package-lock.json')`. Cache com chave fixa guarda dependência velha e produz o
pior resultado possível — **verde que não corresponde ao código**. Na dúvida entre cachear e
não cachear, não cacheie: minuto é barato, confiança não.

## Segredo, permissão e fork

- **Segredo não chega em PR de fork** — é assim de propósito. Trabalho que precisa de segredo
  (publicar, tocar ambiente real) roda **depois** do merge ou em fluxo separado, com aprovação.
- **`pull_request_target` executa com o segredo disponível e o código do PR**: é a armadilha
  clássica de CI. Não use para rodar código de terceiro.
- **Permissão mínima**: declare `permissions: contents: read` no topo e amplie só no job que
  precisa. O padrão amplo dá ao pipeline mais poder do que o trabalho exige.
- **Fixe as *actions* de terceiro** por versão (ou SHA, quando o risco justificar). *Action*
  em `@main` é código de outra pessoa mudando sob o seu gate.
- **Nada de segredo em `echo`, em nome de artefato ou em log.** O mascaramento da plataforma
  ajuda, mas não cobre segredo derivado (`secrets-guard`).

## Tempo e ruído

- `timeout-minutes` em **todo** job. Sem isso, um processo pendurado consome a cota inteira.
- Falha precisa ser legível: o log diz **qual comando** e **qual saída**. Suba o relatório de
  teste como artefato quando a saída for longa.
- **Passo que vive vermelho é pior que passo ausente**, porque ensina a ignorar o vermelho.
  Conserte, ou remova e abra ticket (`micro-ticket-planner`) — não deixe piscando.
- Evite rodar tudo a cada *push* em ramo de rascunho: `paths` e `concurrency` com
  `cancel-in-progress` cortam desperdício sem cortar cobertura.

## O que **não** entra no CI

- **Deploy automático sem gate humano** — vive em `deploy-reproduzivel`, com rollback
  declarado antes.
- **Varredura que sempre acha algo** e ninguém trata: ou vira gate de verdade com limite
  acordado, ou sai.
- **Segredo de produção** para rodar teste. Teste usa ambiente e dado de teste.

## Templates

| Arquivo | Uso |
|---|---|
| `templates/ci.template.yml` | um workflow com os blocos de Python/uv, Rust, C++/CMake e Node/Svelte — apague os que não usa |
| `templates/release.template.yml` | artefato e publicação disparados por tag, com versão vinda da tag |

Ajuste os comandos para **exatamente** os do `AGENTS.md` e rode o verificador.

## O que você vai pensar para afrouxar

| O que você vai pensar | Por que não vale |
|---|---|
| "Esse teste é instável, ponho `continue-on-error`" | Teste instável não vira verde: vira ticket. Passo que não reprova não prova. |
| "O CI é mais lento que rodar local" | Então corrija a ordem e o cache, não o gate. |
| "Deixo o lint fora, o revisor vê" | Revisor humano é o recurso mais caro; gastar com espaço em branco é desperdício. |
| "Cacheio tudo para ganhar tempo" | Cache com chave errada dá verde que não corresponde ao código. |
| "Uso `pull_request_target` para o PR ter acesso ao segredo" | É exatamente como se entrega segredo a código de terceiro. |

## Ligação com o resto do acervo

`gates-de-conclusao` define o que é gate cumprido — o CI é a versão que roda em servidor ·
`definir-stack` dá os comandos que o pipeline executa · `teste-primeiro` produz o teste que o
CI roda · `deploy-reproduzivel` recebe o artefato daqui · `pr-review-guard` confere que o PR
passou no gate antes da revisão humana · `secrets-guard` para segredo no pipeline.

## Definição de pronto da skill

- [ ] Todo comando da ilha `comandos-exatos` do `AGENTS.md` roda no CI (verificador passou).
- [ ] Nenhum passo com `continue-on-error` ou `|| true` mascarando falha.
- [ ] Ordem barato → caro; lint e formatação rodam uma única vez.
- [ ] Matriz existe só onde a plataforma muda o resultado.
- [ ] Chave de cache inclui o *lockfile*.
- [ ] `permissions` mínimo declarado; *actions* de terceiro fixadas por versão.
- [ ] `timeout-minutes` em todos os jobs.
- [ ] Nenhum segredo acessível a PR de fork; nada de `pull_request_target` com código de PR.
- [ ] O pipeline **reprovou** pelo menos uma vez no teste — um gate que nunca falhou não foi
      exercitado.
