<!-- Caminho relativo: skills/didatica/fundamentos.md -->

# Fundamentos da skill `didatica`

De onde vem cada regra do `SKILL.md`, e quanto peso a evidência tem. Pesquisa feita em
2026-11-07. O nível indica o tipo de fonte, não uma nota de qualidade.

## Pedagogia e psicologia da aprendizagem

| Regra da skill | Princípio | Evidência e fonte |
|---|---|---|
| Calibrar antes; partir do que a pessoa sabe | **Aprendizagem significativa** (Ausubel): o fator que mais pesa na aprendizagem é o que o aluno já sabe; o conceito novo se ancora em estruturas existentes. | Teoria clássica, revisitada criticamente em [Bryce & Blown, 2023, *Current Psychology*](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10130311/). |
| Mapa curto do caminho na âncora | **Organizador prévio** (Ausubel): introdução que mostra o que é novo e importante e lembra ideias anteriores relacionadas. | Mesma revisão; ela recomenda adaptar o organizador ao aluno, não à turma. |
| Uma ideia por rodada; o passo acompanha o aluno | **Zona de desenvolvimento proximal e andaime** (Vygotsky; Wood, Bruner & Ross): apoio no intervalo entre o que o aluno faz sozinho e o que faz com ajuda, retirado aos poucos. | Teoria clássica; resumo prático em [eLearning Industry](https://elearningindustry.com/guide-to-vygotskys-zone-of-proximal-development-and-scaffolding) (fonte comercial, só para orientação). |
| Rodadas curtas; ritmo da pessoa | **Princípio da segmentação** (Mayer) e **carga cognitiva** (Sweller): conteúdo em segmentos no ritmo do aluno gerencia o processamento essencial. | Mediana d = 0,79 nas comparações segmentado × contínuo (Mayer & Pilegard, 2014), citado em [Mayer et al., 2017](https://par.nsf.gov/servlets/purl/10061485). Medido com material multimídia; a transposição para diálogo em texto é inferência. |
| Retirar apoio de quem já entendeu | **Efeito de reversão da expertise** (Kalyuga): técnica eficaz para iniciante perde efeito ou atrapalha quem já sabe. | [Kalyuga, 2007, *Educational Psychology Review*](https://doi.org/10.1007/s10648-007-9054-3); [Kalyuga et al., ASU](https://faculty.engineering.asu.edu/mre/wp-content/uploads/sites/31/2020/02/Exp_Rev_LI06.pdf). |
| Exemplo resolvido antes da fórmula geral | **Efeito do exemplo resolvido** (Sweller; Clark & Mayer). | [Cambridge Handbook of Multimedia Learning](https://cambridge.org/core/books/cambridge-handbook-of-multimedia-learning/worked-examples-principle-in-multimedia-learning/8753055D1FB47CF1E2BB897FD44FBEF8). Ressalva da própria literatura: sozinho, pode ficar na superfície; por isso a skill pede a pergunta de verificação. |
| Do concreto ao abstrato | **Concreteness fading** (Fyfe, McNeil et al.): concreto → intermediário → símbolo. | [Fyfe et al., 2014, *Educational Psychology Review*](https://www.doi.org/10.1007/S10648-014-9249-3). Evidência mais forte em matemática e ciências com aluno de pouco conhecimento prévio. |
| Pedir que explique com as próprias palavras; síntese dela no fecho | **Autoexplicação** e **ICAP** (Chi): engajamento construtivo e interativo rende mais que passivo; autoexplicar rende mais que receber explicação. | [Chi & Wylie, 2014, *Educational Psychologist*](https://chilab.asu.edu/sites/default/files/lcl/chiwylie2014icap_2.pdf). |
| Pergunta para responder dias depois | **Prática de recuperação** e espaçamento, avaliados como de alta utilidade por Dunlosky et al., 2013 (*Psychological Science in the Public Interest*). | Revisão citada, não consultada em texto integral nesta pesquisa. |
| Pergunta que revela, não que confirma | **Verificação de entendimento diagnóstica**: a verificação só vale se o resultado mudar o passo seguinte. | Referência prática, [Flip Education](https://flipeducation.ai/in/teaching-wiki/check-for-understanding). |

## Tutoria com IA

| Regra da skill | Achado | Fonte |
|---|---|---|
| Pergunta faz pensar; travou, explica | Acesso livre ao GPT-4 melhorou a prática e **piorou a prova** (−17% contra quem não teve acesso); a versão com salvaguardas (dicas em vez de respostas) anulou quase todo o dano. Ensaio de campo, ~1000 alunos de ensino médio. | [Bastani et al., 2025, *PNAS*](https://papers.ssrn.com/abstract=4895486) |
| Andaime, gestão de carga, uma etapa por vez | Tutor de IA construído sobre as mesmas boas práticas da aula de aprendizagem ativa rendeu cerca do dobro do ganho, em menos tempo. ECR com 194 alunos de física em Harvard, dois tópicos, teste de curto prazo. | [Kestin et al., 2025, *Scientific Reports*](https://michellemillerphd.substack.com/p/r3-37-july-15-2025-how-do-tutoring) (resenha; DOI 10.1038/s41598-025-97652-6) |
| Pedagogia como instrução explícita | "Seguir instrução pedagógica": o comportamento de tutor ideal varia demais para um esquema fixo; descrevê-lo na instrução funciona melhor. Num ECR em cinco escolas do Reino Unido (165 alunos, com tutores humanos revisando cada mensagem), o tutor superou dicas estáticas e empatou ou superou tutores humanos. | [LearnLM, arXiv 2412.16429](https://arxiv.org/pdf/2412.16429); estudo de sala, arXiv 2512.23633 |
| Uma pergunta por vez | Recorrente em modelos de prompt de tutor; não há regra oficial publicada pela Khan Academy, só a descrição do processo de prompt. | [Khan Academy, 7 etapas de prompt do Khanmigo](https://blog.khanacademy.org/pt-br/engenharia-de-prompts-no-khanmigo) |
| Questionamento em vez de resposta pronta | O *Learning mode* do Claude for Education usa perguntas socráticas ("como você abordaria?"). | [VentureBeat](https://venturebeat.com/ai/anthropic-flips-the-script-on-ai-in-education-claude-learning-mode-makes-students-do-the-thinking) |

## Limites desta base

- Os estudos de IA são de **ensino médio e graduação**, com exercício de resposta certa. A
  skill é para explicação de conceito no mestrado, um contexto diferente: aluno com mais
  base, pedido de entendimento e não de nota. A transposição é inferência.
- Nenhum estudo testou **esta** skill. Se a pergunta for "ela muda o meu entendimento?",
  o caminho é `experimento-controlado` (critério escrito antes, braço de controle).
- As regras de forma (15 linhas, um termo por rodada) são **escolhas de projeto** guiadas
  pela segmentação, não números tirados da literatura. Ajuste pelo uso.
