<!-- Caminho relativo: docs/adr/README.md -->

# Índice de ADRs do framework (Registros de Decisão de Arquitetura)

Decisões de arquitetura **do próprio framework** (distintas das ADRs-template incluídas em
cada perfil sob `profiles/*/docs/adr/`). Leitura **obrigatória** antes de propor mudanças
funcionais ao framework (ver skill `adr-writer`). ADRs são imutáveis após `Accepted`; para
reverter, crie um novo ADR e marque o antigo como `Superseded by ADR-NNNN`.

| ADR | Título | Status |
|-----|--------|--------|
| [0001](0001-adocao-de-rtk-para-reducao-de-tokens.md) | Adoção do RTK (proxy CLI em Rust) para redução de consumo de tokens | Proposed |
| [0002](0002-adocao-de-okf-llm-wiki-para-conhecimento-estruturado.md) | Alinhamento ao Open Knowledge Format (OKF / "LLM-Wiki") para conhecimento estruturado | Proposed |
| [0003](0003-perfis-base-overlay.md) | Perfis em modelo base + overlay (descoberta dinâmica e composição) | Proposed |
| [0004](0004-skills-executaveis.md) | Skills executáveis com scripts anexos (declarativo → executável) | Proposed |
| [0005](0005-config-de-servicos-e-skills-overlay.md) | Configuração de serviços locais e skills overlay do projeto | Proposed |
| [0006](0006-artefato-agentry-settings-json-por-perfil.md) | Distribuição de `.agentry/agentry.settings.json` por perfil | Proposed |
| [0007](0007-arquitetura-de-delegacao-por-perfil.md) | Arquitetura de delegação (nuvem planeja, local lê) distribuída por perfil | Accepted |
| [0008](0008-superficie-de-customizacao-do-projeto.md) | Superfície de customização do projeto e separação governança/domínio nas skills | Accepted |
| [0009](0009-hooks-como-sensor-e-skills-como-estrategia.md) | Hooks como sensor e skills como estratégia (par sensor/estratégia) | Proposed |
| [0010](0010-delegacao-a-gateway-litellm.md) | Delegação de volume a gateway LiteLLM como rota distinta da delegação local | Accepted |
| [0011](0011-estado-repo-local-e-excecao-de-segredo.md) | Estado de skill é repo-local; segredo é a única exceção | Accepted |
| [0012](0012-adaptadores-multi-harness.md) | Adaptadores multi-harness (`.claude/skills` + `.agents/skills`) sobre a fonte neutra | Accepted |
| [0013](0013-taxonomia-subagents-e-bibliotecas-multiplas.md) | Taxonomia por categoria, subagents na fonte neutra e bibliotecas múltiplas | Accepted |
| [0014](0014-instalacao-guiada-e-portabilidade.md) | Instalação guiada e portabilidade para macOS e Windows | Accepted |
| [0015](0015-biblioteca-privada-em-repositorio-publico.md) | Biblioteca privada em repositório público ou compartilhado | Accepted |
| [0016](0016-invocacao-declarada.md) | Invocação declarada na skill, traduzida por harness | Proposed |
| [0017](0017-cadeia-spec-driven.md) | Cadeia spec-driven, com a spec como artefato numerado | Accepted |
| [0018](0018-registro-de-recusados.md) | Registro de conceitos recusados, indexado por conceito | Accepted |
| [0019](0019-barra-de-admissao.md) | Barra de admissão de duas pernas | Accepted |
| [0020](0020-roteador-de-skills.md) | Roteador de skills, com sincronia verificada por comando | Accepted |
| [0021](0021-procedencia-do-acervo.md) | Procedência do acervo — amálgama declarado, crédito no artefato | Accepted |
| [0022](0022-selecao-do-acervo-na-instalacao.md) | Seleção do acervo na instalação, derivada do projeto | Proposed |
