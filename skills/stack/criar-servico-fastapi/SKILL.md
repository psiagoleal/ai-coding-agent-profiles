---
name: criar-servico-fastapi
description: >-
  Constrói serviço HTTP em FastAPI com Pydantic v2: rota fina que valida e
  delega, domínio sem framework dentro, erro traduzido na borda, acesso a banco
  parametrizado e configuração por ambiente. Cobre também o contrato OpenAPI que
  o front consome. Aciona ao criar ou alterar endpoint, roteador, dependência ou
  modelo de entrada e saída em projeto FastAPI. NÃO usar para a interface
  (→ criar-ui-sveltekit), para decidir a stack (→ definir-stack), nem para
  desktop (→ criar-app-tauri).
---

# criar-servico-fastapi — a rota é a borda, não o lugar da lógica

Deixado por conta própria, o agente escreve o sistema inteiro dentro da função da rota:
validação, regra de negócio, SQL e formatação de resposta em trinta linhas que só se testam
subindo o servidor. Funciona no primeiro dia e é irrecuperável no terceiro.

## Passo 0 — gate de detecção

```bash
skills/stack/criar-servico-fastapi/scripts/checar-stack.sh    # ou: --raiz backend/
```

Lê `pyproject.toml` ou `requirements.txt` e confere FastAPI e Pydantic v2. Divergiu, pare:
Pydantic v1 tem outra API (`@validator`, `.dict()`, `Config`), e o código de um não roda no
outro.

## Stack alvo

| Camada | Tecnologia | Observação |
|---|---|---|
| Framework | FastAPI · Pydantic v2 | `model_validate`, `model_dump`, `field_validator` |
| Servidor | uvicorn | `--reload` só em desenvolvimento |
| Dependências | uv | `uv sync`, `uv run` |
| Banco | PostgreSQL 16 | sempre parametrizado; role por serviço |
| Migração | Alembic (ou SQL versionado) | nunca DDL no *startup* |
| Teste | pytest + httpx `AsyncClient` | rota e domínio testados separados |
| Qualidade | ruff · mypy | `mypy` no pacote, não só nos testes |

> Confira as versões com o *lockfile*; o gate do passo 0 imprime as que o projeto declara.

## Estrutura

```
src/<pacote>/
├── main.py            ← app, middlewares, handlers de erro, inclusão de rotas
├── config.py          ← Settings (Pydantic) lidas do ambiente
├── deps.py            ← dependências: sessão, usuário, paginação
├── rotas/<recurso>.py ← APIRouter: valida, delega, traduz erro
├── dominio/           ← a regra de negócio — SEM importar fastapi
├── repo/              ← acesso a dado, parametrizado
└── esquemas/          ← modelos Pydantic de entrada e saída
tests/
```

**O domínio não importa `fastapi`.** É a regra que torna o serviço testável sem subir
servidor e permite trocar o transporte depois (fila, CLI, outro framework) sem reescrever a
regra. Um `grep -r "^from fastapi" src/<pacote>/dominio/` que devolva algo é defeito.

## As sete regras que evitam o serviço que não se sustenta

**1. Rota fina.** Recebe modelo de entrada, chama uma função de domínio, devolve modelo de
saída. Se passar de ~15 linhas, tem lógica no lugar errado.

**2. Modelo de entrada ≠ modelo de saída ≠ modelo de banco.** Devolver a entidade do ORM
direto vaza campo que ninguém pretendia expor — `senha_hash`, `interno`, o e-mail de outro
usuário. Declare `response_model` e deixe o FastAPI podar.

**3. Erro do domínio é do domínio; `HTTPException` é da borda.** O domínio levanta o erro
dele; um `exception_handler` traduz para status e corpo. Assim o mesmo domínio serve a outro
transporte, e a mensagem que vai ao cliente não carrega `Traceback` nem SQL.

**4. `async def` só com I/O assíncrono.** Chamada bloqueante (`requests`, driver síncrono,
`time.sleep`, CPU pesado) dentro de rota `async` trava o *event loop* inteiro — é o defeito
de desempenho mais comum em FastAPI. Duas saídas honestas: declare a rota como `def` (o
FastAPI a executa em *threadpool*) ou use cliente assíncrono de verdade.

**5. Configuração vem do ambiente, e falha cedo.** `Settings` do Pydantic, sem valor padrão
para segredo e sem apontar produção por engano. Serviço que sobe com `DEBUG=True` porque a
variável faltou é incidente esperando data (`secrets-guard`).

**6. Toda consulta é parametrizada e toda lista é paginada.** Concatenar valor em SQL é
injeção, mesmo "só neste filtro interno". Lista sem limite é o que derruba o serviço quando a
tabela cresce — limite padrão e máximo, ambos declarados.

**7. Chamada externa tem tempo limite.** Cliente HTTP sem `timeout` espera para sempre e
segura a conexão; some com o tempo de resposta do seu serviço junto.

## Segurança que o revisor procura

- **CORS**: origem explícita. `allow_origins=["*"]` com `allow_credentials=True` é proibido
  pelo próprio navegador e sinaliza configuração copiada sem leitura.
- **Autenticação em dependência**, não repetida em cada rota; autorização perto do domínio,
  onde a regra mora.
- **Tamanho de corpo limitado** (no proxy ou na borda) e *upload* gravado em disco, não em
  memória.
- **`/health` que checa dependência** — banco e serviço externo. Health que devolve 200 fixo
  só informa que o processo está vivo, que é o que ninguém perguntou.
- **Log estruturado com identificador de requisição**, sem dado pessoal e sem segredo no
  corpo registrado.

## O contrato com o front

O OpenAPI é gerado do código: modelo de saída bem declarado **é** a documentação. Para o front
em SvelteKit (`criar-ui-sveltekit`):

- O `+page.server.ts` chama a API **do servidor**, com o token guardado lá; o navegador não
  vê credencial.
- Mesma origem via proxy no desenvolvimento evita CORS por completo — prefira isso a afrouxar
  a política.
- Erro do serviço volta tipado e vira estado de erro na tela, não `alert`.

Mudou a forma de resposta? A mudança é de contrato: versione a rota ou atualize os dois lados
no mesmo trabalho (`spec-como-contrato`).

## Provar que funciona

```bash
uv sync
uv run pytest -q tests/test_<recurso>.py::test_rejeita_corpo_grande   # o caso, no ciclo vermelho
uv run pytest -q --cov=src
uv run ruff check . && uv run mypy src/
uv run uvicorn <pacote>.main:app --reload
```

Teste de rota com `httpx.AsyncClient` cobre o contrato; teste de domínio cobre a regra, sem
app. **O caminho infeliz é obrigatório**: entrada inválida, ausência de permissão, dependência
fora do ar. É onde o agente esquece de testar e onde o serviço quebra.

## Anti-padrões

- Regra de negócio dentro da rota · domínio importando `fastapi`
- Entidade do banco devolvida como resposta · `response_model` ausente
- `except Exception: raise HTTPException(500, str(e))` — devolve detalhe interno ao cliente
- I/O bloqueante em rota `async` · `requests` no lugar de `httpx`
- `create_all()` no *startup* em vez de migração versionada
- Lista sem paginação · consulta montada por concatenação
- Segredo com valor padrão no `Settings` · CORS `*` com credenciais

## Ligação com o resto do acervo

`definir-stack` decide que é serviço web · `criar-ui-sveltekit` consome o contrato daqui ·
`spec-como-contrato` fixa o critério de aceite antes da rota · `teste-primeiro` faz o teste da
rota nascer falhando · `mapa-de-arquitetura` registra a fronteira rota → domínio → repo ·
`secrets-guard` para a configuração · `pr-review-guard` confere resposta sem campo a mais.

## Definição de pronto da skill

- [ ] O gate do passo 0 passou, com a saída lida.
- [ ] Nenhum `import fastapi` dentro de `dominio/`.
- [ ] Toda rota tem `response_model`, e nenhum modelo de banco é devolvido direto.
- [ ] Erro do domínio é traduzido na borda; nenhuma resposta carrega `Traceback` ou SQL.
- [ ] Nenhuma chamada bloqueante dentro de rota `async`.
- [ ] Segredo sem valor padrão; o serviço falha cedo se faltar configuração.
- [ ] Consultas parametrizadas; toda lista tem limite padrão e máximo.
- [ ] Teste do caminho infeliz existe e passou, com a saída citada.
- [ ] `ruff` e `mypy` limpos no pacote.
