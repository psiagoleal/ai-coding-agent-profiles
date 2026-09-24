<!-- Caminho relativo: docs/tickets/MT-3.md -->

# MT-3 — Skill de biblioteca ou CLI em Rust

**Contexto.** 8 repositórios com `Cargo.toml`, incluindo `agentry` e `LT-Sagitta`; o lado Rust do Tauri já está coberto, o resto não.

**Escopo**

- Gate lendo `Cargo.toml` (edição, workspace).
- Erro com `thiserror`, API pública mínima, feature flags.
- Teste com `cargo test`, doc test e `clippy -D warnings`.

**Critério de aceite.** Gate aprova `agentry` e `LT-Sagitta`; skill traz template de erro e de CLI com `clap`.

**Fora de escopo.** O que não estiver acima. Mudança de escopo vira ticket novo, não
crescimento deste.
