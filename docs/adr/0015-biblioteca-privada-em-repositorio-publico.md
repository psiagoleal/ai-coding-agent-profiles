<!-- Caminho relativo: docs/adr/0015-biblioteca-privada-em-repositorio-publico.md -->

# ADR 0015 — Biblioteca privada em repositório público ou compartilhado

- **Status:** **aceito**
- **Data:** 2026-09-24 · aceito em 2026-09-24

## Contexto

Hoje a biblioteca privada só é instalada em repositório privado. Quando um repositório
público ou compartilhado precisa das mesmas skills, esbarramos num detalhe que costuma passar
despercebido: **o conteúdo não é a única coisa que vaza — o nome também.**

Instalar uma skill privada deixa rastro em quatro lugares, todos versionados:

| Lugar | O que aparece |
|---|---|
| `skills/<categoria>/<nome>/` | o nome da skill, no caminho |
| `.claude/skills/<nome>` | idem, no adaptador |
| `.agents/skills/<nome>` | idem, nos demais harnesses |
| `.gitignore`, se listar skill a skill | o nome, em texto, no arquivo que deveria protegê-lo |

A última linha é a armadilha: proteger por nome escreve o nome. Hoje a defesa é o verificador
de vazamento, que roda no pre-commit — controle **de detecção**, que depende de a lista de
nomes privados estar atualizada. Queremos um controle **estrutural**.

## Opções

**A. Ignorar por diretório, e tratar adaptador como artefato gerado.**
Fonte privada em `skills/privado/` (nome genérico, sem informação); `.gitignore` ganha três
linhas fixas — `skills/privado/`, `.claude/skills/`, `.agents/skills/` — iguais em todo
projeto, sem citar skill alguma. Os adaptadores passam a ser **gerados**, não versionados, o
que é coerente com a ADR 0012: eles já são ponteiros derivados da fonte neutra.

- *A favor:* nenhum nome privado entra no repositório, por construção; o diff deixa de ter
  dezenas de symlinks; a mesma regra serve a todo repositório, público ou não.
- *Contra:* quem clona precisa rodar o instalador uma vez para ter as skills no agente — hoje
  o clone já vem pronto. Exige migrar os repositórios que têm `.claude/skills` versionado
  (`git rm --cached`, uma vez por repositório).

**B. Biblioteca privada fora do repositório, em caminho global.**
As skills privadas ficam em `~/.claude/skills` e valem para todas as sessões.

- *A favor:* nada a ignorar; nenhum rastro no repositório.
- *Contra:* contraria a ADR 0011 (estado repo-local, com segredo como única exceção); passa a
  valer em projetos onde não deveria; e o que o agente vê deixa de ser reproduzível a partir
  do repositório — dois desenvolvedores com bibliotecas globais diferentes leem regras
  diferentes no mesmo código.

**C. Manter como está: instalar e confiar no verificador de vazamento.**

- *A favor:* zero mudança.
- *Contra:* depende de lista de nomes atualizada e de o hook estar instalado no clone. Um
  clone novo sem hook publica o nome no primeiro commit.

## Decisão

**Opção A**, com três detalhes:

1. O instalador acrescenta as três linhas ao `.gitignore` do alvo quando instala fonte extra,
   e sempre para os adaptadores. Linhas fixas, iguais em todo projeto.
2. O verificador de vazamento ganha uma checagem nova: se há fonte privada instalada e as
   regras de ignore não estão presentes, **falha** — hoje ele só procuraria os nomes.
3. A migração dos repositórios existentes (`git rm --cached` dos adaptadores) é feita pelo
   `scripts/atualizar-repos.sh`, com `--dry-run` primeiro e repositório a repositório.

## Consequências

**Positivas.** O nome privado deixa de depender de vigilância: ele não tem por onde entrar.
Diffs menores. A regra é a mesma em repositório público e privado, então não há "modo
especial" que alguém esquece de ligar.

**Negativas.** Clone sem instalação não tem skills ativas para o agente — precisa de um passo,
que passa a constar no README. Migração única em ~20 repositórios, com diff a revisar.

**Neutras.** A fonte pública continua versionada; só o adaptador deixa de ser.

## Detalhes fechados na aceitação

- **O nome é `skills/privado/`.** Genérico o bastante: diz que há algo local, não o que é.
- **O passo extra no clone é aceitável**, e passa a constar no README do projeto alvo: uma
  linha de instalação, que já era necessária para quem quisesse o framework atualizado.
- **A migração não é automática.** `scripts/atualizar-repos.sh --migrar-adaptadores` faz o
  `git rm --cached` dos adaptadores, repositório a repositório, com `--dry-run` antes. Nada é
  apagado do disco: só deixa de ser rastreado.
