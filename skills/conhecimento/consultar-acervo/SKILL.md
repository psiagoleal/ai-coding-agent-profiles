---
name: consultar-acervo
description: >-
  Como usar uma base de conhecimento indexada antes de responder: consultar em
  vez de varrer, ler o trecho no arquivo original, citar caminho e proveniência,
  e distinguir "o acervo não diz" de "a busca não achou". Aciona quando existe
  base indexada no projeto e a pergunta é sobre o material dela, ao responder
  sobre histórico, norma ou projeto anterior, e antes de afirmar que algo não
  existe no acervo.
---

# consultar-acervo — o que o acervo diz, com o caminho junto

Base indexada só paga quando a resposta **vem dela**. O modo de falha não é técnico: é o
agente responder de memória sobre um domínio que tem acervo do lado, com a mesma confiança de
quando leu.

## A regra

> **Toda afirmação sobre o acervo vem com o caminho do arquivo que a sustenta.**
> Sem caminho, é memória do modelo — e deve ser dito que é.

## O ciclo da consulta

**1. Busque com o termo do domínio, não com a pergunta.** O índice casa palavras, não
intenção. "Qual a distância mínima ao solo?" vira `"distância mínima" OR "distancia ao solo"`.

**2. Varie a grafia antes de concluir que não existe.** Acervo real tem abreviação,
maiúscula, erro de digitação e termo em duas línguas. Um `OR` a mais custa milissegundos;
concluir "não existe" cedo custa a resposta inteira.

**3. Abra o arquivo.** O trecho da busca serve para escolher, não para responder: ele é
recorte sem contexto, e a tabela que dá sentido ao número costuma estar duas linhas acima.

**4. Cite com proveniência.** Caminho, e **como o texto foi extraído** quando isso muda a
confiança: texto nativo é uma coisa, OCR de digitalização é outra.

**5. Registre a lacuna.** Se a resposta não está no acervo, diga isso — e anote onde
procurou. "Não achei" some no fim da sessão; a lacuna registrada evita a segunda busca igual.

## Três respostas diferentes que costumam virar uma só

| Situação | O que dizer |
|---|---|
| A busca achou e você leu o arquivo | "Segundo `<caminho>`: …" |
| A busca não achou nada | "A busca por `<termos>` não retornou nada — o acervo pode ter isso com outro termo." |
| O tipo de arquivo nem foi indexado | "Isso está em arquivos que a extração não cobre (`estado` mostra os erros por método)." |

Misturar as três produz o pior resultado possível: afirmar que **não existe** algo que só não
foi indexado. Antes de dizer "não existe no acervo", confira o estado da base.

## Orçamento de contexto

Acervo é grande; a janela não é. Leia **trechos**, não documentos: use o resultado para
escolher o arquivo, abra a região relevante, e só leia inteiro o que for curto. Dez resultados
de 300 caracteres custam menos que um PDF inteiro e decidem melhor.

Quando a leitura for volumosa mesmo assim, ela é candidata a delegação — subagente ou
endpoint OpenAI-compatible, com o cuidado de perímetro (`delegacao-a-subagentes`,
`delegacao-openai-compat`).

## Confidencialidade

O trecho que voltou é conteúdo do acervo, com a mesma classificação do original:

- Não cole trecho de material confidencial em commit, documentação pública, *issue* ou
  mensagem para serviço externo.
- Sob NDA, trecho não vira exemplo em documentação nem fixture de teste.
- Credencial encontrada dentro do acervo é incidente, não achado: `secrets-guard`.

## O que você vai pensar para responder sem consultar

| O que você vai pensar | Por que não vale |
|---|---|
| "Eu sei essa norma de cabeça" | O acervo tem a **versão que este projeto usa**, que pode não ser a que você lembra. |
| "A busca não achou, então não existe" | Pode ser grafia, extração ausente ou tipo não indexado. Três coisas diferentes. |
| "O trecho do resultado já responde" | Trecho é recorte sem contexto; o que dá sentido ao número costuma estar ao lado. |
| "Cito depois o arquivo" | Sem o caminho na hora, a afirmação nasce sem origem e ninguém a reconstrói. |

## Ligação com o resto do acervo

`indexar-acervo` constrói e mantém a base · `critico-independente` para quando a conclusão do
acervo decide algo caro · `delegacao-a-subagentes` e `delegacao-openai-compat` para leitura
volumosa · `handoff-updater` para registrar a lacuna encontrada.

## Definição de pronto da skill

- [ ] A base foi consultada **antes** de responder sobre o material dela.
- [ ] Buscou-se mais de uma grafia antes de concluir ausência.
- [ ] O arquivo original foi aberto; a resposta não se apoia só no trecho do resultado.
- [ ] Toda afirmação traz o caminho, e a proveniência quando ela muda a confiança.
- [ ] "Não achei", "não existe" e "não foi indexado" foram ditos como coisas distintas.
- [ ] Lacuna encontrada ficou registrada onde a próxima sessão lê.
- [ ] Nenhum trecho confidencial saiu do perímetro do projeto.
