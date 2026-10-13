<!-- Caminho relativo: docs/interop/isolamento-de-execucao.md -->

# Isolamento de execução — a fronteira que temos, e como medir candidatos contra ela

> **O que é este documento.** Não é uma ADR de adoção, e não propõe uma. É a medição que uma
> ADR precisaria ter e que hoje não existe: **o que o nosso isolamento de fato impede**, dito
> em termos verificáveis, e um gabarito para medir candidatos contra isso.
>
> Escrito porque a ordem inversa é a armadilha. Avaliar `container-use`, microVM ou qualquer
> outra coisa sem ter enunciado a própria fronteira é comparar contra um vazio — e um vazio
> aprova qualquer candidato.
>
> Data: 2026-10-09. Medições em estação Linux de referência, com data indicada caso a caso.

## 1. A fronteira que temos hoje

Três mecanismos, e só o terceiro é uma fronteira no sentido próprio.

| Camada | Mecanismo | O que impede | Quem impõe |
|---|---|---|---|
| Permissão | `deny`/`ask` em `.claude/settings.json` | comando cujo **texto** casa com o padrão | o harness, por casamento de string |
| Hook | `PreToolUse` → `checar-comando-git.sh` | comando de git que altere local ou remoto | nosso script, por casamento de string |
| Diretório | `git worktree` por fatia (`paralelizacao-em-grafo`) | que duas fatias escrevam no mesmo arquivo | o sistema de arquivos |

**Nenhuma das três é uma fronteira de segurança.** As duas primeiras filtram *texto de comando*,
não capacidade; a terceira separa *escrita concorrente*, não privilégio. Um processo dentro de
qualquer uma delas tem o mesmo acesso de rede, o mesmo sistema de arquivos e os mesmos segredos
que o usuário que o lançou.

### 1.1 E o filtro por texto tem defeito medido

A análise comparativa de harness mediu isto no hook de git: **8 de 10 formas de indireção
passam** — `sh -c 'git commit'`, `bash script.sh`, `/usr/bin/git commit`, `xargs`, `eval`. O
remédio está no MT-24.

O ponto aqui é que **a lista `deny` dos perfis usa a mesma superfície de casamento**. Ela nega
`Bash(cat *.env*)`, `Bash(env)`, `Bash(printenv*)` e seis outros. Se a classe de defeito for a
mesma — e não há razão estrutural para não ser —, então a proteção de segredo dos perfis tem o
mesmo furo que o hook tinha.

> **[A MEDIR]** Isto é inferência por analogia estrutural, **não** medição. O hook foi medido;
> a lista `deny` não. Está no §8 como item 1, e é o item mais barato da lista.

## 2. O que o framework já prescreve e nunca implementou

Três linhas do `profiles/externo-confidencial/AGENTS.md`, na seção de segurança:

| Prescrição | Mecanismo hoje |
|---|---|
| "Sandbox recomendada/obrigatória: **contêineres efêmeros** / *worktrees*" | só a metade dos worktrees |
| "Injeção indireta: ***allowlist* de domínios**" | **nenhum** |
| "evitar `--dangerously-skip-permissions`" | parcial — `defaultMode: default` e lista `deny` |

Duas prescrições de três não têm executável. Isso é pior do que não prescrever: a frase no
perfil induz a crer que a proteção existe. É a mesma classe de defeito que a nossa própria ADR
de não-adoção nomeia — **suporte parcial que parece completo** — aplicada a nós mesmos.

Este documento existe principalmente por causa desta tabela. A pergunta não é "adotamos uma
ferramenta nova?", é "temos duas regras escritas que não valem nada; o que as faria valer?".

## 3. As classes de motor, e por que a classe é a variável

Um estudo comparativo de junho de 2026 mediu cinco produtos em seis eixos de propriedade de
motor — superfície de ataque no hospedeiro, vazamento de informação, empilhabilidade de
defesas, histórico de CVE, cadência de correção e postura de *fuzzing*.

Achado estrutural: **as classes separam limpo em todos os eixos arquiteturais; produtos dentro
da mesma classe não separam.**

| Classe | Motor | Fronteira | Consequência prática |
|---|---|---|---|
| Contêiner OCI | `runc` | namespaces + cgroups, **kernel compartilhado** | trocar um invólucro de Docker por outro não muda nada |
| Kernel em espaço de usuário | gVisor (Sentry) | syscalls atendidas por kernel intermediário | custo em carga pesada de syscall; lacunas de compatibilidade |
| microVM | Firecracker, Cloud Hypervisor, libkrun | kernel próprio sobre KVM | custo na partida, não por syscall |

Para o nosso caso a leitura é direta: ferramenta que orquestra Docker **é da classe do
contêiner OCI**, qualquer que seja o seu transporte. Chamar-se "MCP para contêineres" descreve
como o agente fala com ela, não o que ela isola.

O `runc` tem padrão de recorrência registrado: o trio de escapes de 2025-11 (`CVE-2025-52565`,
`CVE-2025-52881`, `CVE-2025-31133`, corrida de procfs/mount) e, antes, `CVE-2024-21626`
("Leaky Vessels").

## 4. A variável dominante não é a classe — é quem fixa a versão

Segundo achado do mesmo estudo, e é o que mais muda a nossa decisão:

> A política de *pin* do produto é a variável dominante para o operador: a latência de correção
> do lado do motor agrega ≈0 dias para divulgações coordenadas, enquanto o atraso do lado de
> baixo vai de 0 dias a 471+ dias, a "opaco", a ∞.

Traduzido para uma instalação mantida por uma pessoa: **o risco mora menos no motor escolhido e
mais em quem repassa a correção dele.** Um produto intermediário que fixa um motor que não
controlamos pode ficar mais de um ano atrás, ou nunca atualizar, sem que isso apareça.

Isso pesa a favor de **primitivas que a distribuição corrige** e contra invólucros que
introduzem um elo de *pin* a mais. É um critério de manutenção, não de arquitetura, e por isso
mesmo é o que sobrevive ao tempo.

## 5. O que a estação já tem

Verificado em 2026-10-09, por comando, em estação Linux de referência:

| Recurso | Situação | Habilita |
|---|---|---|
| KVM acessível | presente | classe microVM é viável localmente |
| Landlock ativo como LSM | sim | sandbox de primitivas do SO |
| `bubblewrap` | instalado | idem — **testado**: rede bloqueada dentro do sandbox |
| `socat` | instalado | ponte dos proxies sobre soquete Unix |
| Docker | instalado | classe contêiner OCI |
| `podman`, `runsc`, `firecracker` | ausentes | — |

**O teste, não a dedução:** um `bwrap` com `--unshare-net` sobre a raiz em modo leitura
devolveu resolução de nome falhando dentro do sandbox. Funciona apesar de a restrição AppArmor
a *user namespaces* não privilegiados estar ativa, porque o bubblewrap tem perfil próprio.

Conclusão operacional: **a camada de primitivas do SO custa zero de instalação aqui.** A camada
de microVM custa instalação, mas não está bloqueada por falta de hardware.

## 6. A restrição que elimina metade dos candidatos

A nossa arquitetura de delegação depende de alcançar um gateway interno. Qualquer isolamento
que desligue a rede inteira **quebra a delegação**, que é uma capacidade que o framework usa de
propósito, não um efeito colateral.

Isso descarta os desenhos de rede tudo-ou-nada — inclusive o bloqueio por seccomp do Codex CLI,
que não tem granularidade por domínio, e o Seatbelt do macOS pela mesma razão. O que serve é
**lista de permissão de saída**, e na prática isso significa um proxy fora do sandbox.

É também, note-se, exatamente o mecanismo que a linha "*allowlist* de domínios" do perfil
prescreve e nunca teve. As duas necessidades são a mesma necessidade.

## 7. Os candidatos, medidos contra o §1

Gabarito: o que cada um acrescenta à fronteira que já temos, não o que promete.

| Candidato | Classe | Acrescenta sobre o §1 | Custo de *pin* | Veredito |
|---|---|---|---|---|
| `container-use` (Dagger) | contêiner OCI | fluxo de branch por agente; isolamento de sistema de arquivos no nível do Docker | elo a mais: fixa Docker/`runc` | **não adotar agora** — §7.1 |
| Sandbox nativo do harness | primitivas do SO | sistema de arquivos + rede por domínio, via proxy | segue a distro | **experimentar** |
| `srt` (`sandbox-runtime`) | primitivas do SO | idem, para **processo arbitrário** | segue a distro + npm | **experimentar primeiro** — §7.2 |
| `krunvm` / `microsandbox` | microVM | fronteira de kernel, de verdade | pré-1.0, *pin* próprio | candidato para o perfil confidencial |
| Sandlock | primitivas do SO | ACL de rede em nível HTTP, diretório copy-on-write | acadêmico, sem adoção | acompanhar |

### 7.1 Por que `container-use` não entra agora

Três razões, em ordem de peso:

1. **Classe errada para a promessa.** Herda a fronteira do Docker e não acrescenta nada a ela.
   O que ele acrescenta é fluxo de trabalho — contêiner e branch por agente —, e fluxo de
   trabalho é o que já temos com worktrees.
2. **Colide com regra adotada.** Ele opera dando ao agente branch e commits próprios. A regra
   dos três perfis, adotada em 2026-10-07, diz que o agente propõe git e a pessoa executa, e o
   hook recusa. Adotar sem resolver isso publica duas doutrinas contraditórias — o mesmo
   problema que o MT-36 tem de resolver entre a ADR 0009 e a do hook.
3. **Fronteira não enunciada.** A documentação dele não diz o que acontece com acesso de rede,
   exposição do sistema de arquivos do hospedeiro, nem tratamento de segredo; e o projeto se
   declara experimental, em desenvolvimento inicial, com quebras esperadas.

Nada disso é objeção ao projeto. É objeção a adotá-lo **como resposta à linha "contêineres
efêmeros" do perfil confidencial**, que é a vaga que ele pareceria preencher e não preenche.

### 7.2 Por que o experimento começa pelo `srt`

Contraintuitivo e vale registrar: o invólucro publicado pela Anthropic prende menos a um agente
do que a ferramenta MCP. Ele embrulha **processo arbitrário** — agente, servidor MCP local,
comando de shell —, então serve igualmente para os outros harness que o nosso instalador
atende. O critério de não nos prendermos a um agente é atendido pela forma do executável, não
pela origem dele.

Padrão de negar: sem rede e sem escrita fora dos caminhos previstos. Permissão de saída por
domínio com porta, por proxy HTTP e SOCKS5 fora do sandbox, com conferência do endereço
resolvido contra classes negadas — laço local, *link-local*, metadados de nuvem — o que fecha
*DNS rebinding* para dentro da rede interna.

Limitações declaradas por ele, que precisam entrar em qualquer ADR que o adote: é "Beta
Research Preview"; no Linux o bubblewrap **não reporta violação** (depurar é procurar `EPERM`
com `strace`); globs de `denyRead` são expandidos no momento do embrulho e não cobrem arquivo
criado depois; o bloqueio de `AF_UNIX` por seccomp só vale em x64/arm64.

## 8. O que falta medir, em ordem de custo

1. **A lista `deny` dos perfis contra indireção.** Mesmo gabarito do hook de git — `sh -c`,
   caminho absoluto, `xargs`, `eval` — aplicado aos nove padrões de segredo. É o item mais
   barato e o de maior consequência, porque decide se a proteção de segredo dos perfis é real
   ou nominal. Hoje é **inferência**, não medição (§1.1).
2. **Embrulhar um agente com `srt`, com o gateway na lista de saída, no perfil pessoal**, e
   registrar o que quebra. Uma tarde, reversível. Produz a linha de base que falta.
3. **Repetir (2) com um segundo harness**, para separar o que é limitação do sandbox do que é
   dependência do agente.
4. **Medir a classe microVM** (`krunvm` ou `microsandbox`) contra o mesmo gabarito, só então, e
   só para o perfil confidencial.
5. **Enunciar a fronteira resultante por perfil**, e **só aí** escrever a ADR de adoção.

A ordem importa. Um a quatro são medição e são reversíveis; cinco é decisão. Inverter é como
mudar quatro coisas no mesmo merge — e a análise que deu origem a este documento já mostrou o
que isso custa: causalidade não é provável retroativamente.

## 9. O que uma ADR de adoção teria de decidir

Registrado aqui para que a ADR não precise redescobrir:

1. **Fronteira por perfil, declarada.** `pessoal`, `empresa` e `externo-confidencial` não
   precisam da mesma classe. O que não pode é um perfil prometer uma classe e entregar outra.
2. **A lista de saída é configuração do perfil, não do agente.** Mesma razão pela qual papel
   não decide rota: quem pode falar com quem é política, e política não mora no artefato que
   ela restringe.
3. **O que acontece quando o sandbox não está disponível.** Degradar em silêncio é o defeito
   que a guarda de vazamento foi escrita para não cometer. A resposta provável é recusar no
   perfil confidencial e avisar nos outros — mas é decisão, não decorrência.
4. **Quem fixa a versão, e como se percebe que ficou para trás** (§4). Sem isso, a ADR escolhe
   um motor e herda uma dívida invisível.

## Fontes

- Estudo comparativo de sandboxes de código de IA, Parte 1 — propriedades de motor:
  `arXiv:2606.08433`. Mede cinco produtos em três classes; **declara explicitamente que não
  propõe ranking geral**, e foi usado aqui para separar classes, não para eleger produto.
- Sandlock — confinamento com primitivas Linux não privilegiadas: `arXiv:2605.26298`. Números
  auto-relatados pelos autores.
- `anthropic-experimental/sandbox-runtime` — README e limitações declaradas.
- Documentação de sandbox do Claude Code e de arquitetura de sandbox do Codex CLI.
- `dagger/container-use` — README e página de introdução.
