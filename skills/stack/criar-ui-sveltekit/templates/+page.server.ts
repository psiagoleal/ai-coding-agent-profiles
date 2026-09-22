// Caminho relativo: src/routes/<recurso>/+page.server.ts
// Modelo da skill criar-ui-sveltekit: load no servidor, action com validação e erro tipado.
// Este arquivo NUNCA chega ao navegador — é aqui que segredo e acesso a banco podem morar.
import { fail, error } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { listar, criar } from '$lib/server/repositorio';

export const load: PageServerLoad = async ({ locals, url }) => {
  // Dado inicial vem daqui — não de fetch no onMount.
  const pagina = Number(url.searchParams.get('pagina') ?? '1');
  if (!Number.isInteger(pagina) || pagina < 1) error(400, 'página inválida');

  return { itens: await listar({ pagina, usuario: locals.usuario }) };
};

export const actions: Actions = {
  criar: async ({ request, locals }) => {
    const dados = await request.formData();
    const nome = String(dados.get('nome') ?? '').trim();

    // Validação na borda: devolve o que o formulário precisa para se repintar.
    if (!nome) return fail(400, { nome, erro: 'informe o nome' });

    try {
      const item = await criar({ nome, usuario: locals.usuario });
      return { sucesso: true, id: item.id };
    } catch (e) {
      // Erro de infraestrutura não vira 200 silencioso.
      error(500, 'não foi possível criar o item');
    }
  },
};
