---
name: criar-ui-sveltekit
description: >-
  Constrói interface em SvelteKit 2 com Svelte 5 (runes), TypeScript estrito e
  os tokens do docs/DESIGN.md: rotas, carregamento de dados no servidor, ações
  de formulário com aprimoramento progressivo, componentes com props tipadas e
  testes com Vitest e Playwright. Aciona ao criar página, rota, componente ou
  formulário em projeto SvelteKit. NÃO usar para decidir a stack
  (→ definir-stack), para definir cor, tipografia ou token (→ contrato-de-design),
  nem para lógica de servidor sem interface.
---

# criar-ui-sveltekit — interface em SvelteKit 2 / Svelte 5

Esta skill é a **execução**. O contrato visual vem do `docs/DESIGN.md`
(`contrato-de-design`) e não se decide aqui; a escolha da stack vem de `definir-stack`.

## Passo 0 — gate de detecção (não pule)

```bash
skills/stack/criar-ui-sveltekit/scripts/checar-stack.sh    # ou: --raiz frontend/
```

Ele lê o `package.json` do projeto e confere SvelteKit e Svelte 5. **Saiu diferente, pare** e
volte a `definir-stack`: escrever `.svelte` com runes num projeto Svelte 4 gera código que
não compila, e num projeto React gera lixo. Não deduza a stack pelo nome das pastas.

## Stack alvo

| Camada | Tecnologia | Observação |
|---|---|---|
| Framework | SvelteKit 2 · Svelte 5 (runes) | `$state`, `$derived`, `$props`, `$effect` |
| Linguagem | TypeScript 5 ou 6, estrito | `strict: true`; `any` só com comentário justificando |
| Build | Vite 6 a 8 | quem manda é o do projeto; o gate imprime a versão |
| Estilo | CSS com os tokens do `DESIGN.md` | `<style>` com escopo; sem valor cru |
| Teste unitário/componente | Vitest + `@testing-library/svelte` | |
| Teste de ponta a ponta | Playwright | fluxo, não unidade |
| Checagem | `svelte-check` | aviso de acessibilidade tratado como erro |

> Versões conferidas em **2026-09-22** contra os projetos desta máquina (Svelte 5 em todos,
> SvelteKit 2, Vite 6/7/8, TS 5/6). A skill não manda na versão instalada — o gate do passo 0
> lê o *lockfile* e manda.
>
> **Aplicação desktop (Tauri 2):** a interface segue esta skill; o lado Rust, a ponte de
> comandos e as permissões **não** estão cobertos aqui — ver o ticket do painel.

## Estrutura

```
src/
├── routes/
│   ├── +layout.svelte          ← moldura; importa os tokens uma vez
│   ├── +page.svelte            ← marcação; sem fetch de dados inicial
│   ├── +page.server.ts         ← load() e actions — roda só no servidor
│   └── <recurso>/[id]/+page.svelte
├── lib/
│   ├── components/<Nome>.svelte
│   ├── server/                 ← só servidor; importar daqui no cliente é erro de build
│   └── tipos.ts
└── app.css                     ← camadas primitiva e semântica do DESIGN.md
```

## Regras que evitam o código que o agente escreve por hábito

**1. Dado inicial vem do `load`, não do `onMount`.** Buscar no `onMount` custa uma tela vazia,
quebra a renderização no servidor e duplica tratamento de erro. `+page.server.ts` quando
precisa de segredo ou banco; `+page.ts` quando o dado é público.

**2. Runes, não *stores*, para estado local.** `$state` para o que muda, `$derived` para o que
se calcula a partir dele. `$effect` é o último recurso — se ele só recalcula um valor, era
`$derived`. *Store* continua válida para estado compartilhado entre rotas.

**3. Props tipadas com `$props()`**, com valor padrão explícito:

```svelte
<script lang="ts">
  let { rotulo, variante = 'primaria', aoClicar }: {
    rotulo: string; variante?: 'primaria' | 'perigo'; aoClicar?: () => void;
  } = $props();
</script>
```

**4. Formulário é `<form>` com *action***, aprimorado por `use:enhance` — funciona sem
JavaScript e o erro volta tipado. `fetch` manual em `on:submit` é o caminho que perde
validação, estado de carregamento e acessibilidade de uma vez.

**5. Segredo nunca atravessa para o cliente.** `$env/dynamic/private` só em `+*.server.ts` ou
`$lib/server/`. Toda variável em `+page.svelte` chega ao navegador (`secrets-guard`).

**6. Estilo consome token.** `var(--acento)`, nunca `#3b82f6`. Valor que não existe no
`DESIGN.md` não entra no componente: ou se acrescenta lá, ou não é para existir.

**7. Estado vazio, de carregamento e de erro são parte do componente**, não um segundo
ticket. É o que a receita do `DESIGN.md` exige e o que o revisor procura.

## Comandos

```bash
npm run dev                  # servidor de desenvolvimento
npm run check                # svelte-check — tipos e acessibilidade
npx vitest run src/lib/components/Botao.test.ts   # um teste (ciclo do teste-primeiro)
npx playwright test          # ponta a ponta
npm run build && npm run preview
```

Ajuste ao projeto e registre na ilha `comandos-exatos` do `AGENTS.md` **o que você rodou**.

## Templates

| Arquivo | Uso |
|---|---|
| `templates/Componente.svelte` | componente com props tipadas, estados e estilo por token |
| `templates/+page.server.ts` | `load` e `action` com validação e erro tipado |

## Anti-padrões

- `fetch` no `onMount` para dado inicial · `$effect` fazendo o trabalho de `$derived`
- `{@html}` com conteúdo de usuário (injeção) · `any` para calar o verificador de tipos
- Componente que acumula lógica de servidor · lógica de domínio dentro de `.svelte`
- Aviso de acessibilidade silenciado com comentário em vez de corrigido
- Token novo criado no componente em vez de no `DESIGN.md`

## Ligação com o resto do acervo

`definir-stack` decide que é SvelteKit · `contrato-de-design` dá os tokens · `teste-primeiro`
manda o teste de componente nascer falhando · `mapa-de-arquitetura` registra a fronteira entre
`lib/server` e o resto · `pr-review-guard` confere estado vazio, acessibilidade e valor cru.

## Definição de pronto da skill

- [ ] O gate do passo 0 passou, com a saída lida.
- [ ] Dado inicial vem de `load`; nenhum `fetch` de carga inicial em `onMount`.
- [ ] Props tipadas via `$props()`; nenhum `any` sem justificativa no código.
- [ ] Formulário funciona sem JavaScript (`<form>` + action) antes de receber `use:enhance`.
- [ ] Nenhum valor cru de cor, fonte ou espaço fora dos tokens.
- [ ] Estados vazio, carregando e erro implementados.
- [ ] `npm run check` sem erro nem aviso de acessibilidade, com a saída citada.
- [ ] Teste de componente ou de ponta a ponta novo para o comportamento alterado.
