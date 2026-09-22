<!-- Caminho relativo: docs/adr/0014-instalacao-guiada-e-portabilidade.md -->

# ADR 0014 — Instalação guiada e portabilidade para macOS e Windows

- **Status:** aceito
- **Data:** 2026-09-22

## Contexto

O instalador só era usável por quem já sabia o que queria: exigia perfil e alvo na linha de
comando, e falhava em dois sistemas sem dizer o porquê.

Levantamento do script (803 linhas) apontou quatro incompatibilidades reais:

| Construção | Onde quebra |
|---|---|
| `declare -A`, `mapfile` | macOS, cujo `/bin/bash` é 3.2 |
| `sed -i` sem argumento | BSD/macOS, que exige `-i ''` |
| `sha256sum` | macOS, que traz `shasum -a 256` |
| `find -printf` | BSD/macOS, que não tem a opção |

No Windows, o symlink do adaptador exige Modo de Desenvolvedor, e o usuário só descobria
isso pelo erro.

## Decisão

1. **Exigir bash ≥ 4, mas procurar sozinho.** Antes de falhar, o script tenta
   `/opt/homebrew/bin/bash`, `/usr/local/bin/bash` e `/usr/bin/bash`, testando a versão antes
   de reexecutar. Sem candidato, a mensagem diz o comando do sistema (`brew install bash`).
   Reescrever 803 linhas para bash 3.2 custaria mais do que vale, e emular array associativo
   com `eval` traz defeito sutil.
2. **Isolar as diferenças GNU/BSD em quatro funções** — `sha256_de`, `sed_inplace`,
   `dirs_com_skill`, `nomes_de_agents` — decididas uma vez, por teste real de capacidade, não
   por nome de sistema operacional.
3. **`--doctor`**: diagnóstico que verifica bash, git, jq, python3, suporte a symlink no alvo
   e se o alvo é repositório git, imprimindo o comando de instalação **do sistema detectado**.
4. **Modo guiado** quando o script roda sem argumentos e há terminal interativo: pergunta
   perfil pela árvore de decisão, alvo, oferece `git init`, escolhe `--skills-mode` pelo teste
   de symlink, mostra a prévia resumida e pede confirmação. Sem terminal (CI, script), o
   comportamento antigo é preservado: imprime o uso e sai.

## Consequências

**Positivas.** Instalação possível em macOS e Windows sem conhecimento prévio; erro de
pré-requisito vira instrução acionável; o caminho interativo não exige memorizar opções.

**Negativas.** macOS sem bash moderno precisa de um passo extra (`brew install bash`). O modo
guiado acrescenta caminho a manter, e ele **não** é coberto por teste automático — foi
exercitado por pty (`script -qec`) na implantação.

**Neutras.** A forma direta continua idêntica, então nada do que já existia muda.
