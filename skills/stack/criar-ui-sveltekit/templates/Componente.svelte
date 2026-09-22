<!-- Caminho relativo: src/lib/components/<Nome>.svelte
     Modelo da skill criar-ui-sveltekit: props tipadas, estados obrigatórios, estilo por token. -->
<script lang="ts">
  type Variante = 'primaria' | 'perigo';

  let {
    rotulo,
    variante = 'primaria',
    carregando = false,
    desabilitado = false,
    aoAcionar,
  }: {
    rotulo: string;
    variante?: Variante;
    carregando?: boolean;
    desabilitado?: boolean;
    aoAcionar?: () => void;
  } = $props();

  // $derived, não $effect: é valor calculado, não efeito colateral.
  const bloqueado = $derived(desabilitado || carregando);
</script>

<button
  class="botao {variante}"
  type="button"
  disabled={bloqueado}
  aria-busy={carregando}
  onclick={aoAcionar}
>
  {carregando ? 'Enviando…' : rotulo}
</button>

<style>
  /* Só token semântico — nenhum valor cru. Ver docs/DESIGN.md. */
  .botao {
    padding: var(--espaco-2) var(--espaco-4);
    border: 1px solid transparent;
    border-radius: var(--raio-campo);
    background: var(--acento);
    color: var(--texto-sobre-acento);
    font: inherit;
    cursor: pointer;
  }
  .botao.perigo { background: var(--perigo); }
  .botao:disabled { opacity: 0.6; cursor: not-allowed; }
  /* Foco visível é requisito de acessibilidade — nunca remova sem substituto. */
  .botao:focus-visible { outline: 2px solid var(--acento); outline-offset: 2px; }
</style>
