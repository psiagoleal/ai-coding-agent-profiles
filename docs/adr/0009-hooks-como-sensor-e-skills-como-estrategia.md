<!-- Caminho relativo: docs/adr/0009-hooks-como-sensor-e-skills-como-estrategia.md -->

# ADR 0009: Hooks como sensor e skills como estratégia (par sensor/estratégia)

- **Status:** Proposed <!-- pendente de uso em campo antes de Accepted -->
- **Data:** 2026-09-04
- **Decisores:** Iago Leal (mantenedor), com Claude Code
- **Tags:** skills, hooks, observabilidade, custo, portabilidade

## Contexto

A biblioteca hoje distribui **skills** (`SKILL.md` + `scripts/`, ADR 0004) e artefatos de
configuração por perfil (`.agentry/agentry.settings.json`, ADR 0006). Nenhum ADR trata de
**hooks** — o mecanismo pelo qual o próprio harness executa um comando num evento do ciclo
de vida da sessão.

O caso motivador é a **cota de uso da conta** (janelas de 5h e 7d). O percentual existe só no
payload da barra de status e **não chega ao contexto do modelo**, que por isso planeja como se
a cota fosse infinita e responde "não tenho essa visibilidade".

Uma skill sozinha não resolve. Skills são carregadas por **divulgação progressiva**: o agente
só expande o corpo quando a tarefa casa com a `description`. Mas o agente **não sabe** que a
cota está apertada — esse é justamente o dado que falta — então o gatilho nunca dispara
sozinho. Quando o usuário pensa em perguntar, o trabalho já está no meio.

A alternativa examinada foi um hook `SessionStart` injetando a cota no início de toda sessão.
Foi **descartada** pelo mantenedor: no início da sessão a informação raramente é necessária, e
injetá-la sempre é ruído constante para cobrir um caso raro.

## Decisão

> **Proposta (não ratificada).** O framework pode distribuir **hooks** como *adaptador por
> agente* de uma skill, sob o padrão **sensor/estratégia**, condicionado à validação da
> Diretriz de Conformidade.

### 1. Papéis separados
- **Skill = estratégia.** Conhecimento operacional: como interpretar o dado e o que fazer.
  Portátil (`SKILL.md`), independente de agente, carregada sob demanda.
- **Hook = sensor.** Só decide **quando** a estratégia precisa acordar. Não carrega
  conhecimento; aponta para a skill.

O hook sem a skill entrega número sem conduta; a skill sem o hook entrega conduta tarde
demais. O par é a unidade útil.

### 2. Padrão *gate*: silêncio é a saída esperada
Todo hook distribuído em evento de alta frequência (`UserPromptSubmit` e afins) roda em modo
**gate**: **não imprime nada** abaixo de um limiar e só emite uma linha quando cruza. Sem
saída, nada entra no contexto — o custo em sessão tranquila é o do processo, não o de tokens.
Limiar configurável por flag e por env var.

### 3. Falha silenciosa obrigatória
O hook roda no caminho crítico do prompt do usuário. Erro, dependência ausente ou provedor
inexistente resultam em **saída vazia e código 0**, nunca em mensagem de erro ou prompt
quebrado. O comando distribuído termina em `2>/dev/null || true` e declara `timeout`.

### 4. Leitura agnóstica ao agente
O script do sensor esconde a origem do dado atrás de uma lista de **provedores**, cada um
devolvendo um dicionário normalizado ou `None`. Suportar outra ferramenta é acrescentar um
provedor; a skill e o hook não mudam. Sem provedor, a resposta é um `no_data` limpo.

### 5. Fonte única, ponteiro por agente
O script vive na skill (fonte neutra). A instalação pessoal e o adaptador do agente são
**symlinks** para ele — mesma política já adotada para `.claude/skills/`. Sem cópias
divergentes.

### 6. Skill de referência
`skills/limites-de-uso/` (governança) é o exemplo canônico do padrão: `SKILL.md` com a
estratégia, `scripts/usage-limits.py` com os modos de leitura e o `--gate` do hook.

## Consequências

- **Impacto positivo:** o agente passa a planejar com a restrição real à vista, e o aviso
  chega **antes** do trabalho longo, não depois da interrupção.
- **Impacto positivo:** o padrão sensor/estratégia é reutilizável — qualquer condição
  observável localmente (disco cheio, serviço fora do ar, branch divergente) cabe no molde.
- **Impacto negativo (latência):** um processo por prompt. Medido em ~19 ms neste caso;
  aceitável, mas é um teto que precisa ser respeitado (ver Diretriz).
- **Impacto negativo (portabilidade):** hooks são específicos de cada agente. O `SKILL.md`
  continua portátil; o hook é adaptador descartável, e um agente sem hooks perde só o
  despertar automático — a skill continua utilizável sob demanda.
- **Trade-off aceito:** rejeitou-se injeção no `SessionStart` (simples, porém ruidosa) em
  favor do gate por limiar (silencioso, porém com um processo por prompt).

## Diretriz de Conformidade de Código

- **Obrigatório:** hook em evento de alta frequência roda em modo *gate* e **não imprime nada**
  no caso comum. Saída incondicional a cada prompt é proibida.
- **Obrigatório:** falha silenciosa. Nenhum caminho do hook pode escrever em stderr visível,
  retornar código diferente de 0, ou bloquear o prompt. Declare `timeout`.
- **Obrigatório — orçamento de latência:** o sensor deve custar **< 50 ms** por invocação.
  Acima disso, mova o trabalho para fora do caminho do prompt (cache em arquivo, evento de
  frequência menor). Meça antes de distribuir.
- **Obrigatório:** o sensor **só lê** — arquivo local, modo somente-leitura. Sem I/O de rede,
  sem escrita, sem leitura de credenciais. Um hook roda a cada prompt: qualquer efeito
  colateral é multiplicado e invisível.
- **Obrigatório:** o dado devolvido carrega **idade** e o consumidor a verifica. Número
  defasado apresentado como atual é pior que a ausência de número.
- **Obrigatório:** projeção ou extrapolação declara **confiança** e a base amostral; projeção
  de base curta é apresentada como indício, nunca como previsão.
- **Proibido:** hook que injete contexto incondicionalmente "porque é barato". O critério é
  necessidade no momento, não custo unitário.
- **Proibido:** duplicar o script entre a skill e o diretório do agente. Use ponteiro.

> Qualquer desvio desta regra viola as diretrizes de conformidade arquitetural do projeto
> e deve ser reportado para revisão antes de prosseguir.

## Referências

- Skills executáveis e invocação por interpretador: [ADR 0004](0004-skills-executaveis.md)
- Adaptadores por agente como symlink: `skills/README.md`
- Skill de referência: `skills/limites-de-uso/SKILL.md`
