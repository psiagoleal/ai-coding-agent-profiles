Temos um hook que recusa comando git que altera estado, executado pelo agente. Ele casa `git`
**ancorado em posição de comando**: no início da linha ou logo depois de `&&`, `;`, `|`, `$(`
ou crase, com opções globais (`-C x`, `-c k=v`) entre o `git` e o verbo.

Um terceiro publicou uma guarda com o mesmo objetivo que casa a **substring** `git push` (e
outras) em qualquer lugar da linha, sem âncora. Sabemos que a guarda dele:

- bloqueia `grep -rn "git push" docs/` — falso positivo, é só leitura;
- deixa passar `git  push origin main`, com espaço duplo.

Pergunta: incorporar o mecanismo de casamento dele traz algum ganho para a nossa guarda, ou
seria só importar o defeito? Responda e diga como chegou à resposta.
