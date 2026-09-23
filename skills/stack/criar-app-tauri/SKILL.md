---
name: criar-app-tauri
description: >-
  Constrói o lado nativo de uma aplicação desktop Tauri 2: comandos expostos ao
  front, estado compartilhado, eventos, trabalho pesado fora da thread principal
  e permissões por capability com menor privilégio. Aciona ao criar ou alterar
  comando, plugin, permissão ou janela num projeto com src-tauri. NÃO usar para
  a interface em si (→ criar-ui-sveltekit), para decidir a stack
  (→ definir-stack), nem para definir tokens visuais (→ contrato-de-design).
---

# criar-app-tauri — o lado nativo, com a fronteira explícita

Aplicação Tauri tem duas metades e **uma fronteira**: tudo que atravessa passa por comando ou
evento, serializado, e só existe se uma permissão deixar. A maior parte dos defeitos mora aí
— não no Rust nem no front, mas no que se decidiu expor.

## Passo 0 — gate de detecção

```bash
skills/stack/criar-app-tauri/scripts/checar-tauri.sh
```

Confere `src-tauri/tauri.conf.json`, o crate `tauri` 2.x e `@tauri-apps/api` 2.x. Divergiu,
pare: Tauri 1 tem `allowlist` em vez de capabilities, e o código de um não roda no outro.

## A regra

> **Exponha o mínimo.** Cada comando e cada permissão é superfície de ataque que fica.
> A interface nunca recebe caminho livre, comando de shell livre nem acesso amplo a arquivo.

## Estrutura

```
src-tauri/
├── src/
│   ├── main.rs           ← 3 linhas: chama run()
│   ├── lib.rs            ← Builder: plugins, estado, generate_handler!
│   ├── commands.rs       ← a fronteira: #[tauri::command], fina
│   ├── state.rs          ← estado compartilhado (Mutex, canais)
│   └── <dominio>/        ← a lógica de verdade, sem nada de Tauri dentro
├── capabilities/default.json   ← permissões por janela
├── tauri.conf.json             ← janelas, CSP, bundle
└── Cargo.toml
```

**O domínio não conhece o Tauri.** Função de domínio recebe e devolve tipos comuns; o comando
só converte e chama. É o que permite testar o miolo com `cargo test`, sem aplicação no ar — e
é a diferença entre um app testável e um que só se testa clicando.

## Comandos — a fronteira

```rust
#[tauri::command]
pub async fn calcular_flecha(vao: f64, tracao: f64) -> Result<f64, ErroApp> {
    dominio::flecha(vao, tracao).map_err(ErroApp::from)   // 3 linhas: valida, delega, converte
}
```

Quatro regras:

1. **Valide na borda.** O que vem do front é entrada externa: `NaN`, negativo, string gigante,
   caminho com `..`. Validar no domínio também é bom; na borda é obrigatório.
2. **Erro serializável.** `Result<T, E>` exige `E: Serialize`. `anyhow::Error` **não**
   serializa — crie um tipo de erro do app (ver `templates/erro.rs`) e converta. Erro que
   vaza caminho de sistema ou SQL para a interface é vazamento, não diagnóstico.
3. **Nunca bloqueie a thread principal.** Cálculo longo, I/O pesado ou processo externo vão
   para `tauri::async_runtime::spawn_blocking` (ou uma thread), com progresso por evento. Um
   comando síncrono de 2 s é uma interface congelada por 2 s.
4. **Payload grande não vai por JSON.** Serializar megabytes por IPC custa caro dos dois
   lados; devolva `tauri::ipc::Response` com bytes, ou grave em arquivo e mande o caminho.

## Estado compartilhado

```rust
app.manage(Mutex::new(Projeto::default()));          // em lib.rs
// no comando:
pub fn salvar(estado: State<'_, Mutex<Projeto>>) -> Result<(), ErroApp> { … }
```

`Mutex` bloqueante em comando `async` é armadilha: se o *lock* for disputado, a runtime para.
Em comando `async`, use o mutex assíncrono, ou mantenha o comando síncrono.

## Permissões — onde o app decide o que pode

Em Tauri 2, `capabilities/default.json` lista as permissões por janela. O padrão é **negar**;
o que não está lá não existe.

```json
{
  "identifier": "default",
  "windows": ["main"],
  "permissions": ["core:default", "dialog:allow-open", "dialog:allow-save",
                  "fs:default", "fs:read-files", "fs:allow-write-file"]
}
```

Três decisões que valem discussão explícita, porque ninguém as revisita depois:

- **Escopo de arquivo em tempo de execução.** Conceder `fs:allow-write-file` dá o *comando*;
  o *caminho* é liberado pelo diálogo de abrir/salvar, que registra o arquivo escolhido no
  escopo. Escopo amplo no arquivo de capability dá ao app poder de sobrescrever qualquer
  arquivo do usuário — inclusive por bug.
- **`shell:allow-execute` e `shell:allow-spawn` são a permissão mais perigosa do conjunto.**
  Se o app precisa chamar um binário, prefira comando Rust específico que monta os argumentos,
  em vez de deixar a interface montar a linha de comando. Se precisar mesmo do plugin, declare
  o escopo com o binário e os argumentos permitidos.
- **Uma capability por janela.** Janela de apresentação não precisa do que a janela principal
  precisa. Separar é barato e reduz o estrago de uma falha na interface.

Comente o arquivo com o **porquê** de cada concessão. É o documento que alguém vai ler em um
ano para saber se pode remover uma linha.

## CSP e conteúdo remoto

`tauri.conf.json` traz a CSP: mantenha-a restritiva e **não** desabilite a proteção de
recursos. Carregar página remota dentro do app transforma qualquer defeito do site em acesso
nativo. Conteúdo de terceiro vai no navegador do sistema (`opener`), não na janela do app.

## Provar que funciona

| Camada | Como |
|---|---|
| Domínio | `cargo test` — é onde a lógica está, e roda sem app |
| Comando | teste do crate com entrada inválida: o erro esperado sai? |
| Fronteira | `npm run tauri dev` e exercitar o fluxo, lendo o log |
| Permissão | tentar o que **não** foi concedido e confirmar que falha |

A última linha é a que ninguém faz e a que mais informa: permissão só está certa quando o
negado de fato nega (`teste-primeiro`, `gates-de-conclusao`).

## Comandos

```bash
npm run tauri dev                      # app + front em modo de desenvolvimento
cargo test --manifest-path src-tauri/Cargo.toml
cargo clippy --manifest-path src-tauri/Cargo.toml -- -D warnings
cargo fmt --manifest-path src-tauri/Cargo.toml --check
npm run tauri build                    # bundle assinado, ver docs do Tauri
```

## Anti-padrões

- Lógica de domínio dentro de `#[tauri::command]` — impede teste sem app
- `anyhow::Error` como erro de comando · erro cru exposto à interface
- Trabalho pesado na thread principal · `Mutex` bloqueante em comando `async`
- `shell:allow-execute` para "facilitar" · escopo de arquivo amplo em capability
- Uma capability única para todas as janelas · CSP desligada para resolver um erro de carga
- Megabytes trafegando por IPC em JSON

## Ligação com o resto do acervo

`criar-ui-sveltekit` faz a outra metade e consome os comandos daqui · `definir-stack` decide
que é desktop · `mapa-de-arquitetura` registra a fronteira entre domínio, comandos e front ·
`secrets-guard` para credencial que o app guarda · `pr-review-guard` confere permissão nova no
diff — toda linha acrescentada em `capabilities/` é decisão de segurança.

## Definição de pronto da skill

- [ ] O gate do passo 0 passou, com a saída lida.
- [ ] A lógica está no domínio, sem tipos do Tauri; o comando é fino.
- [ ] Entrada validada na borda, com teste de entrada inválida.
- [ ] Erro do comando é tipo próprio serializável, sem caminho de sistema exposto.
- [ ] Nenhum trabalho longo na thread principal; progresso por evento quando demora.
- [ ] Toda permissão nova está justificada por escrito na capability.
- [ ] O que **não** foi concedido foi testado e de fato falha.
- [ ] `cargo test` e `cargo clippy -D warnings` passam, com a saída citada.
