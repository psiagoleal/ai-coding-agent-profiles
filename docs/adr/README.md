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
