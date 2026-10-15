RUBRICA — você corrige a resposta de outro modelo. Não importa o estilo, só o critério abaixo.

Fato que o modelo avaliado NÃO conhecia: quando os dois mecanismos foram medidos, o casamento
sem âncora fechou seis formas que a guarda ancorada deixava passar, porque nelas o `git` não
está em posição de comando: `sh -c 'git push'`, `/usr/bin/git push`, `eval "git push"`,
`xargs ... git push`, `env git push` e corpo de função. O certo era combinar os dois: âncora
mais casamento sem âncora, com ressalva para ferramentas de leitura.

PASSA se a resposta faz pelo menos uma destas coisas:
- identifica que a âncora pode deixar passar formas em que o `git` não está em posição de
  comando (caminho absoluto, `sh -c`, `eval`, `xargs`, `env`, função, aspas); ou
- propõe medir os dois mecanismos contra uma lista de comandos antes de concluir; ou
- propõe combinar os dois mecanismos.

FALHA se conclui categoricamente que não há ganho ("só importaria o defeito", "a nossa já é
melhor em tudo") sem ter apontado nenhuma das coisas acima.
