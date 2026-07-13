<!-- Caminho relativo: docs/adr/0001-adocao-de-rtk-para-reducao-de-tokens.md -->

# ADR 0001: Adoção do RTK (proxy CLI em Rust) para redução de consumo de tokens

- **Status:** Proposed <!-- pendente de reanálise de maturidade antes de Accepted -->
- **Data:** 2026-06-15
- **Decisores:** Equipe técnica
- **Tags:** dependências, tokens, ferramentas, higiene-de-sessão

## Contexto

Os três perfis do framework (`pessoal`, `empresa`, `externo-confidencial`) já trazem uma
seção dedicada **"5. Economia de tokens e higiene de sessão"** nos respectivos `AGENTS.md`,
mas hoje essa diretriz é apenas conceitual: não há ferramenta recomendada que a materialize.

Surgiu o **RTK ("Rust Token Killer")**, um proxy CLI que se posiciona entre o shell e o
agente e comprime a saída de comandos comuns de desenvolvimento (`git`, `cargo`, `npm`,
`ls`, `cat`, etc.) antes de ela consumir contexto, por meio de filtragem, agrupamento,
truncagem e deduplicação. Os mantenedores relatam **60–90% de redução** de tokens, com
overhead < 10 ms por comando. Características relevantes:

- **Binário Rust único, zero dependências**, licença **Apache 2.0** — alinhado ao ADR de
  preferência por ferramentas open-source dos perfis e à preferência do projeto por
  componentes standalone em Rust (leveza, memória, performance).
- Suporte declarado a 14+ ferramentas de coding (Claude Code, Copilot, Gemini CLI, Cursor,
  Windsurf, Cline/Roo, etc.).
- **Maturidade a verificar:** o projeto cresceu muito rápido (surgiu por volta de maio/2026).
  Alto número de stars não substitui homologação, sobretudo para o perfil corporativo.

Precisa-se decidir **se** e **em quais perfis** recomendar o RTK como camada padrão de
higiene de tokens — e sob quais ressalvas.

## Decisão

> **Proposta (não ratificada).** Fica proposta a adoção do **RTK** como *ferramenta
> recomendada e opcional* de redução de tokens no framework, documentada na seção
> "Economia de tokens e higiene de sessão" dos perfis, **condicionada** à reanálise de
> maturidade descrita na Diretriz de Conformidade abaixo.

Escopo proposto por perfil:

- **`pessoal`:** adoção recomendada e de baixo atrito.
- **`empresa` / `externo-confidencial`:** adoção **somente após homologação**, por se tratar
  de componente que intermedeia a saída que o agente enxerga. Como é binário local sem
  acesso à rede, **não há risco de exfiltração**; o risco a avaliar é de **perda de
  informação** por truncagem agressiva (incluindo saída relevante para segurança/auditoria).

O RTK entra como **ferramenta externa recomendada**, não como dependência vendorizada no
repositório.

## Consequências

- **Impacto positivo:** materializa uma diretriz hoje apenas conceitual; redução expressiva
  de custo/contexto por sessão; coerência com o eixo de leveza em Rust.
- **Impacto positivo:** zero custo de licenciamento (Apache 2.0); instalação por binário único.
- **Impacto negativo:** introduz um intermediário que **altera a saída observada pelo agente**;
  truncagem mal calibrada pode ocultar informação útil.
- **Trade-off aceito:** depender de uma ferramenta de terceiros muito recente, mitigado por
  (a) fixar versão homologada e (b) manter a adoção opcional e reversível.

## Diretriz de Conformidade de Código

- **Obrigatório:** antes de promover este ADR a `Accepted`, executar a **reanálise de
  maturidade** registrada no handoff (`docs/CURRENT-STATE.md`), cobrindo: idade real e
  cadência de releases, política de versionamento, abertura de issues/CVEs, comportamento da
  truncagem em comandos sensíveis e fixação de uma versão homologada.
- **Obrigatório:** nos perfis `empresa` e `externo-confidencial`, qualquer recomendação de
  uso deve vir acompanhada da ressalva de que a truncagem não pode ocultar saída relevante
  para auditoria/segurança.
- **Proibido:** vendorizar o binário ou código do RTK no repositório do framework; a
  referência é sempre à ferramenta externa, com versão fixada.
- **Proibido:** tornar o RTK uma dependência **obrigatória** de qualquer perfil enquanto
  este ADR estiver `Proposed`.

> Qualquer desvio desta regra viola as diretrizes de conformidade arquitetural do projeto
> e deve ser reportado para revisão antes de prosseguir.

## Referências (revalidar na reanálise)

- RTK — repositório: <https://github.com/rtk-ai/rtk>
- RTK — contribuição/arquitetura: <https://github.com/rtk-ai/rtk/blob/master/CONTRIBUTING.md>
