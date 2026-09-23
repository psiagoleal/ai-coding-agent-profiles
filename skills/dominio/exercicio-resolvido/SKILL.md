---
name: exercicio-resolvido
description: >-
  Resolve exercício de engenharia em três artefatos que se sustentam: notebook
  com sympy mostrando fórmula → substituição → resultado para cada grandeza,
  guia por questão em Markdown com a derivação passo a passo e o que o exercício
  ensina, e a fronteira do que fica com o aluno para ele conseguir defender o
  trabalho. Aciona ao resolver lista, prelab, prova antiga ou problema de
  disciplina; ao pedir "notebook com as contas", "guia passo a passo" ou
  "explica a derivação"; e antes de entregar qualquer cálculo acadêmico.
---

# exercicio-resolvido — a conta à vista, e o aluno capaz de defendê-la

Resultado numérico correto entregue sozinho é o pior produto possível num contexto acadêmico:
não ensina, não se confere e não se defende na arguição. Os três artefatos existem para que a
**derivação** seja o entregável, e o número, a consequência.

## A regra

> **Fórmula, substituição e resultado — nesta ordem, para toda grandeza.**
> E o que exige julgamento fica com o aluno, declarado.

## Os três artefatos

| Artefato | Papel | Quem escreve |
|---|---|---|
| `analise/<questao>.py` (+ `.ipynb`) | a conta, executável e conferível | agente |
| `<questao>_guia.md` | a derivação explicada, passo a passo | agente |
| Escolha de topologia, análise crítica, conclusão | o julgamento de engenharia | **o aluno** |

O notebook **acompanha** o script; não o substitui. O script roda no terminal e serve de
conferência rápida; o notebook mostra o caminho.

## 1. Notebook: fórmula → substituição → resultado

Para **cada** grandeza, três exibições em sequência:

**(a) A fórmula**, só com símbolos — é onde se vê de que cada coisa depende.
**(b) A substituição**, com os números no lugar dos símbolos, **sem avaliar**. É o passo que o
aluno confere na calculadora e o que revela erro de unidade.
**(c) O resultado**, numérico, com unidade.

Use `scripts/passo.py`:

```python
import sympy as sp
from passo import mostrar

I_S, G_S, G_L, B_S, B_L = sp.symbols("I_S G_S G_L B_S B_L", real=True)
P_L = I_S**2 * G_L / (2 * ((G_S + G_L)**2 + (B_S + B_L)**2))

mostrar("P_L", P_L, {I_S: 0.08, G_S: 0.01333, G_L: 0.01333, B_S: -0.005526, B_L: 0.005526},
        unidade="W")          # imprime as três linhas e devolve o valor
```

Regras que mantêm o notebook honesto:

- **Símbolos com domínio declarado** (`positive=True`, `real=True`): sympy só simplifica
  radical e módulo quando sabe o sinal, e sem isso a expressão sai feia ou errada.
- **Um símbolo por grandeza física**, com o mesmo nome do enunciado e do guia. Nome divergente
  entre os três artefatos é a causa mais comum de confusão na arguição.
- **Unidade explícita** na exibição e **conferida na entrada**: sympy não sabe que você passou
  nH onde a fórmula espera H.
- **Prefira decimal a fração** nos valores substituídos: `sp.Rational` costuma cancelar sozinho
  e apaga justamente o passo (b).
- **Encadeie o valor cheio, exiba o arredondado.** `mostrar` devolve precisão cheia e arredonda
  só na tela; passe adiante o **retorno**, nunca o número que você leu. Encadear o arredondado
  propaga o erro e faz a verificação final fechar "quase" — e aí o aluno conclui que o projeto
  está impreciso quando o impreciso era o `print`. (Campo, 2026-09-23: resíduo de 3e-5 Ω num
  projeto de rede L, contra erro nulo no script equivalente.)
- **Texto entre as contas**, em Markdown: por que esta fórmula, o que se espera do resultado.
  Notebook só com código é script com mais passos.
- **Verificação independente** ao menos uma vez por questão: limite conhecido, caso particular
  com resposta sabida, ou ordem de grandeza. Número que ninguém checou é chute formatado.

Execute antes de entregar — notebook com célula não executada, ou com saída de uma versão
antiga do código, é erro que o professor vê primeiro:

```bash
uv run --with sympy --with jupyter jupyter nbconvert --execute --to notebook --inplace <arq>.ipynb
```

## 2. Guia por questão

Um arquivo por questão, em Markdown com `$...$` — que o navegador do repositório renderiza e
**não** depende de LaTeX instalado. Estrutura (ver `templates/guia.template.md`):

1. **Título que nomeia a tensão do problema**, não "Questão 3". O título já ensina.
2. **Passo 0 — enquadramento.** Por que esta representação e não outra (admitância e não
   impedância, fasor e não tempo). É o passo que evita o aluno lutar contra o problema errado.
3. **Um passo por etapa da derivação**, cada um com a equação **e o porquê**. Quando a
   expressão final importa, destaque-a em `\boxed{}`.
4. **A resposta em destaque**, com unidade.
5. **"O que o exercício está realmente ensinando"** — o resultado central em uma frase, e o
   trade-off em **tabela**, que é o formato que responde rápido em prova.
6. **Armadilhas** — numeradas, específicas, cada uma dizendo o que acontece se cair nela
   ("se puser $+$, acha um indutor em vez de um capacitor").
7. **"Para você fechar"** — a tarefa manual que o aluno faz sozinho, e o comando que confere
   os números.
8. **Fechamento com a declaração de uso de IA**, conforme a regra da disciplina.

O guia cita o script que gerou os números (`> Números conferidos por [...](...)`). Guia e
notebook que discordam é defeito grave: eles são a mesma verdade em duas formas.

## 3. A fronteira — o que o agente não faz

A disciplina pode anular a atividade se o aluno não souber defendê-la. Então:

- **Escolha de topologia, análise crítica e conclusão são do aluno.** O agente pode apresentar
  alternativas com o trade-off; escolher, não.
- **O guia mostra a derivação**, nunca só o resultado. Se um passo foi "por inspeção", diga
  qual inspeção.
- **Toda seção que o aluno precisa assinar fica marcada** no texto — por exemplo
  `<!-- SEU TEXTO: comparar com o Lab 06 e concluir -->`.
- **Exercício com solução dupla é onde a fronteira cai melhor.** Quando duas soluções são
  matematicamente equivalentes e a escolha é de engenharia (qual topologia, qual ramo da
  raiz), monte a tabela de trade-off completa e deixe **a decisão** marcada como do aluno: o
  guia fica completo sem decidir por ele. Procure esse caso — ele costuma existir.
- **Declaração de uso de IA** em todo entregável, no formato que a disciplina exige.
- **Nada de material de terceiro versionado**: enunciado, PDF e figura do professor ficam fora
  do repositório público (`.gitignore`); cite pela referência, não pela cópia.

## O que você vai pensar para pular a ordem

| O que você vai pensar | Por que não vale |
|---|---|
| "O número já está certo, o resto é enfeite" | O número é o que menos vale: é o que ele não consegue defender sozinho. |
| "Mostro a fórmula e o resultado, a substituição é óbvia" | É na substituição que mora o erro de unidade e de fator ½. |
| "Escrevo a conclusão para ele revisar" | Conclusão revisada não é conclusão defendida — e é exatamente o que a regra proíbe. |
| "Notebook é redundante com o script" | O script dá o número; o notebook dá o caminho. São produtos diferentes. |
| "Rodo o notebook depois" | Saída velha em célula nova é o erro mais visível que existe. |

## Ligação com o resto do acervo

`aula-audio` transforma o guia em roteiro locutado · `spec-como-contrato` quando o trabalho é
um projeto, não uma lista · `critico-independente` para conferir a derivação em contexto limpo ·
`gates-de-conclusao` para a execução do notebook como gate antes de entregar.

## Definição de pronto da skill

- [ ] Cada grandeza aparece como fórmula, substituição e resultado — nesta ordem.
- [ ] Os símbolos têm domínio declarado e o mesmo nome no notebook, no script e no guia.
- [ ] Unidades conferidas na entrada e exibidas na saída.
- [ ] Ao menos uma verificação independente por questão (limite, caso particular ou ordem de
      grandeza).
- [ ] O notebook foi **executado** antes de entregar, sem saída remanescente de versão antiga.
- [ ] O guia tem passo 0, derivação passo a passo, resposta destacada, o que o exercício
      ensina, armadilhas e "para você fechar".
- [ ] Guia e notebook dão os mesmos números.
- [ ] Seções de julgamento estão marcadas como do aluno, e a declaração de uso de IA está no
      entregável.
- [ ] Nenhum material de terceiro foi versionado.
