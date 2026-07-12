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
