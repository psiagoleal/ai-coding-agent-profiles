<!-- Caminho relativo: docs/adr/0002-adocao-de-okf-llm-wiki-para-conhecimento-estruturado.md -->

# ADR 0002: Alinhamento ao Open Knowledge Format (OKF / padrão "LLM-Wiki") para conhecimento estruturado

- **Status:** Proposed <!-- pendente de reanálise de maturidade antes de Accepted -->
- **Data:** 2026-06-15
- **Decisores:** Equipe técnica
- **Tags:** dados, conhecimento, formato, interoperabilidade, documentação

## Contexto

O framework já organiza conhecimento para agentes em **Markdown com YAML frontmatter** e
cross-links: os artefatos `docs/adr/`, o handoff `docs/CURRENT-STATE.md` e o sistema de
memória (com campo `type:` e referências `[[...]]`) seguem, na prática, um padrão muito
próximo do que agora foi formalizado externamente.

O **Open Knowledge Format (OKF)** é uma especificação aberta e *vendor-neutral* anunciada
pelo **Google Cloud** (v0.1, junho/2026) que representa conhecimento como **um diretório de
arquivos Markdown com YAML frontmatter** — um campo obrigatório (`type`) e poucos opcionais
(`title`, `description`, `resource`, `tags`, timestamps), com o corpo em Markdown livre. O
OKF formaliza o padrão **"LLM-Wiki"** popularizado por **Andrej Karpathy**: camadas de
*raw sources* imutáveis → *wiki* gerada e interligada → *schema* (em CLAUDE.md), com
operações de **ingest / query / lint**. Para domínios de conhecimento estáveis, relata-se
redução de até ~95% de tokens frente ao carregamento ingênuo de documentos, pois o agente
lê conhecimento compilado e cross-linkado em vez de redescobrir relações a cada consulta.

Precisa-se decidir **se** o framework adota as convenções do OKF nos seus artefatos de
conhecimento e **se** introduz uma skill de curadoria estilo "LLM-Wiki".

## Decisão

> **Proposta (não ratificada).** Fica proposto **alinhar as convenções de conhecimento do
> framework ao OKF** (frontmatter com `type` obrigatório e campos canônicos), e avaliar a
> criação de uma skill `knowledge-curator` que mantenha uma "LLM-Wiki" do projeto
> (operações *ingest / query / lint*), **condicionado** à reanálise de maturidade abaixo.

Princípios da proposta:

- Adotar as **convenções abertas** do OKF (o formato Markdown+frontmatter), **sem** acoplar
  o framework a *tooling* proprietário do Google Cloud (ex.: Knowledge Catalog).
- Reaproveitar o que já existe: o sistema de memória e a skill `handoff-updater` já são
  parentes diretos de, respectivamente, o frontmatter do OKF e o "lint" da LLM-Wiki.

## Consequências

- **Impacto positivo:** interoperabilidade com um padrão aberto emergente sem reescrever a
  base atual (a distância é pequena); potencial redução adicional de tokens em domínios estáveis.
- **Impacto positivo:** formaliza e dá nome a um padrão que o projeto já praticava de forma implícita.
- **Impacto negativo:** OKF é **v0.1, com poucos dias de vida** — a especificação deve mudar;
  alinhar cedo demais a uma versão instável gera retrabalho.
- **Trade-off aceito:** adotar as *convenções* (estáveis e simples) agora, mas **não** casar
  com a versão exata da spec nem com ferramentas proprietárias até a spec amadurecer.

## Diretriz de Conformidade de Código

- **Obrigatório:** antes de promover este ADR a `Accepted`, executar a **reanálise de
  maturidade** registrada no handoff (`docs/CURRENT-STATE.md`), cobrindo: estabilidade da
  spec OKF (mudanças entre versões), campos efetivamente obrigatórios, e o delta concreto
  entre o frontmatter atual do projeto e o do OKF.
- **Obrigatório:** qualquer adoção deve preservar a independência do framework frente a
  *tooling* proprietário — o OKF é adotado como **formato aberto**, não como integração com
  produto específico.
- **Proibido:** introduzir dependência de serviço proprietário (ex.: Knowledge Catalog) como
  requisito para usar o conhecimento do projeto.
- **Proibido:** quebrar os artefatos existentes (ADRs, handoff, memória) por uma migração
  de formato enquanto este ADR estiver `Proposed`.

> Qualquer desvio desta regra viola as diretrizes de conformidade arquitetural do projeto
> e deve ser reportado para revisão antes de prosseguir.

## Referências (revalidar na reanálise)

- OKF — anúncio/visão (Google Cloud Blog):
  <https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/>
- Knowledge Catalog (diretório `okf`): <https://github.com/GoogleCloudPlatform/knowledge-catalog>
- Padrão "LLM-Wiki" (gist de Andrej Karpathy):
  <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
