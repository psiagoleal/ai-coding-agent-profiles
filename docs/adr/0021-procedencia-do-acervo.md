<!-- Caminho relativo: docs/adr/0021-procedencia-do-acervo.md -->

# ADR 0021: Procedência do acervo — amálgama declarado, com crédito no artefato quando houver

- **Status:** Accepted
- **Data:** 2026-10-11
- **Decisores:** Iago Leal (mantenedor), com Claude Code
- **Tags:** procedência, licença, skills, governança

## Contexto

O acervo não nasceu de uma fonte só, e fingir que nasceu é o que trava a sua manutenção.
Material parado por procedência não resolvida é material que ninguém consegue nem publicar nem
descartar, porque a pergunta "de onde veio isto?" não tem resposta registrada no lugar onde se
precisa dela.

A biblioteca de terceiros analisada tem a **forma** de um campo de crédito no frontmatter, e a
usa em uma skill de trinta e oito. Existe o molde; não existe o sistema.

## Decisão

> **O acervo é declaradamente um amálgama**: aprendizado e material acumulados na experiência
> profissional do mantenedor, mais material de repositórios públicos conhecidos. A declaração
> vale para as fontes atuais **e futuras**.

### Propriedade: o que entra no acervo é nosso

Skill importada de qualquer fonte, depois de analisada e adaptada, é **nossa**, e é tratada
como propriedade nossa. A procedência é declarada pelo que esta ADR estabelece; ela registra
**de onde veio o aprendizado**, não quem manda no artefato.

O motivo de olhar acervo de terceiros é um só: **melhorar o nosso**. Toda skill de fora é
analisada por inteiro — a que tem o mesmo objetivo que uma nossa é comparada ponto a ponto,
para aprimorar a nossa ou para substituí-la quando a dela for melhor. Nenhuma entra por ser de
fora, e nenhuma fica de lado por ser de fora.

O acervo é **um**, distribuído por dois repositórios. A diferença entre eles é apenas se o
material pode ser exposto em repositório público — não é diferença de dono, de estado nem de
qualidade. Material já analisado e importado não é "material de terceiros guardado aqui": é
acervo.

### 1. A declaração de origem, e o que ela não diz

A origem é descrita pela **natureza** da fonte, nunca pela identificação de empregador,
cliente ou projeto empresarial. "Experiência profissional do mantenedor" é a formulação
completa; não há versão mais específica em repositório público.

Para fonte pública, o contrário: identificação completa, com licença e endereço.

### 2. O crédito no artefato — opcional, com campos fixos

```yaml
metadata:
  origem:
    fonte: <repositório ou "experiência profissional do mantenedor">
    autor: <quando houver>
    licenca: <quando houver>
    url: <quando houver>
    importada_em: AAAA-MM-DD
    modificada: sim | não
```

O campo é **opcional**. Quando presente, os nomes são estes — campo com nome inventado é pior
que campo ausente, porque não é agregável.

### 3. `docs/interop/PROCEDENCIA.md` é a fonte principal

Tabela de skill, fonte, licença e situação. É o que se consulta e o que decide publicação.

### 4. O limite desta decisão, declarado

Crédito opcional **não resolve** a deriva entre artefato e registro: uma skill importada sem o
campo não é detectável por comando, e o documento depende de alguém lembrar de atualizá-lo.
Isto é escolha consciente de atrito baixo, não ausência de problema. **Se a triagem em curso
trouxer material em volume**, o documento passa a ser carga pesada mantida à mão, e o momento
de reabrir esta decisão é esse — por ADR nova, com a evidência de quantos itens ficaram sem
registro.

## Consequências

**Positivas.** A pergunta de origem tem resposta padrão, aplicável a fonte futura sem decisão
nova. Material de licença clara entra com atrito baixo. Nenhum artefato público identifica
projeto empresarial.

**Negativas.** Sem verificador, o registro envelhece. A licença continua sendo análise humana:
o campo declara, não prova.

**Relação com outros itens.** Substitui a parte de política do MT-30 e dá à triagem do MT-39 o
vocabulário que faltava para decidir item a item.
