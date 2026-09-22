---
name: indexar-acervo
description: >-
  Constrói uma base de conhecimento local e consultável a partir de um acervo de
  arquivos — inventário com proveniência, extração de texto com o método
  registrado, índice full-text em SQLite/FTS5 e retomada incremental. Sem
  serviço externo e sem mover o acervo. Aciona ao precisar pesquisar um acervo
  grande de documentos, ao pedir "indexar", "base de conhecimento", "buscar nos
  projetos antigos", ou quando o agente está varrendo diretórios com find e grep
  para achar informação que deveria estar indexada.
---

# indexar-acervo — o acervo vira base consultável, e continua no lugar

Um acervo de dezenas de milhares de arquivos não cabe em contexto e não se lê por varredura:
cada `grep -r` custa minutos, devolve caminho sem texto e não guarda nada para a próxima
sessão. A base resolve isso uma vez.

## A regra

> **Indexar não é copiar.** O acervo fica onde está; a base guarda texto extraído, caminho e
> proveniência. Todo resultado de busca aponta para o arquivo original.

## As quatro etapas

```
inventariar  →  extrair  →  indexar  →  consultar
(o que existe)  (texto + método)  (FTS5)  (skill consultar-acervo)
```

Cada etapa é **retomável** e grava o que já fez. Acervo grande cai no meio — por memória,
por arquivo corrompido, por rede. Etapa que precisa recomeçar do zero não termina nunca.

**1. Inventariar.** Uma linha por arquivo: caminho, nome, extensão, tamanho, data, raiz,
projeto, categoria. Hash só quando for preciso detectar duplicata — em arquivo grande, hash
parcial (primeiros e últimos blocos) resolve por uma fração do custo.

**2. Extrair.** Texto por extensão, com o **método registrado junto**: nativo, conversor,
OCR. Saber que um PDF veio de OCR muda quanto se confia no trecho. Registre também o erro
quando a extração falha — arquivo que falhou não é arquivo inexistente, e a diferença importa
na hora de responder "não achei".

**3. Indexar.** SQLite com FTS5 dá busca por frase, prefixo, proximidade e ranking em um
arquivo único, sem serviço no ar. Em acervo em português, use
`tokenize = "unicode61 remove_diacritics 2"`: sem isso, "distancia" não acha "distância", e o
acervo real tem grafia inconsistente.

**4. Estado.** Um comando que diz quantos arquivos, quantos extraídos, quantos com erro e
quantos indexados. É o que permite retomar sem adivinhar.

## O script de referência

```bash
skills/conhecimento/indexar-acervo/scripts/acervo.py inventariar ~/acervo --raiz-nome projetos
skills/conhecimento/indexar-acervo/scripts/acervo.py extrair --limite 500
skills/conhecimento/indexar-acervo/scripts/acervo.py indexar
skills/conhecimento/indexar-acervo/scripts/acervo.py estado
```

Cobre texto, Markdown, CSV, JSON e código; PDF quando houver `pdftotext`; DOCX e XLSX quando
houver as bibliotecas. É ponto de partida: acervo com formato próprio (CAD, planilha com
fórmula, formato proprietário) pede extrator próprio — acrescente um ramo e **registre o
método no banco**, que é o contrato do resto.

O banco padrão é `.cache/acervo/acervo.db`, repo-local (ADR 0011), e **não se versiona**: é
derivado e costuma ser grande. Quem versiona é o inventário, se você quiser rastrear o que
existia.

## Decisões que valem a pena tomar antes

| Decisão | Recomendação |
|---|---|
| Full-text ou vetores? | Comece por full-text. Ele é explicável, reproduzível e barato; vetor entra quando a busca por termo comprovadamente falha (sinônimo, paráfrase). |
| Onde mora a base? | Perto do acervo, fora do repositório de código, e no `.gitignore`. |
| O que é "projeto" e "categoria"? | Defina **antes** de inventariar: são os filtros que tornam a busca usável. Em geral, projeto = diretório de primeiro nível; categoria = tipo de material. |
| Indexar o quê? | Só o que se lê. Binário, imagem sem OCR e dado bruto entram no inventário, não no índice. |

## Confidencialidade

O acervo costuma ser mais sensível que o código. Sob perfil confidencial:

- A base fica **local**. Nada de serviço de embedding na nuvem, nada de subir o texto para
  API de terceiro (`delegacao-a-subagentes` decide o que pode sair).
- O banco entra no `.gitignore` **e** no `.claudeignore`.
- Trecho extraído é conteúdo do cliente: não vira fixture de teste, exemplo em documentação
  nem mensagem de commit.

## O que você vai pensar para pular a base

| O que você vai pensar | Por que não vale |
|---|---|
| "`grep -r` resolve" | Resolve uma vez, e você paga de novo na próxima sessão — sem ranking e sem texto de PDF. |
| "Indexo depois, agora só preciso de um arquivo" | O terceiro "só um arquivo" já custou mais que o índice. |
| "Preciso de embeddings para isso" | Meça primeiro: em acervo técnico com vocabulário estável, FTS5 costuma bastar. |
| "Copio os arquivos para dentro do projeto" | Duplica dado sensível e cria duas verdades. |

## Ligação com o resto do acervo

`consultar-acervo` é o outro lado — como perguntar e como citar · `secrets-guard` para
credencial encontrada dentro do acervo · `delegacao-a-subagentes` para o que pode sair da
máquina · `gates-de-conclusao` para a extração longa, que precisa de orçamento e critério de
parada.

## Definição de pronto da skill

- [ ] Inventário com proveniência: caminho, raiz, projeto, categoria.
- [ ] Extração registra o **método** e o **erro**, por arquivo.
- [ ] Índice FTS5 criado com remoção de diacríticos, em acervo em português.
- [ ] Todas as etapas são retomáveis e há um comando de estado.
- [ ] A base está fora do versionamento e, se confidencial, no `.claudeignore`.
- [ ] Nenhum conteúdo do acervo saiu da máquina sem decisão explícita.
- [ ] O caminho original é recuperável a partir de qualquer resultado.
