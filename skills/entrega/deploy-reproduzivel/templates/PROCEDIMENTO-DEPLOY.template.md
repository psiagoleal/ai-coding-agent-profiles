<!-- Caminho relativo: docs/PROCEDIMENTO-DEPLOY.md -->

# Procedimento de deploy — <serviço>

> Preenchido **antes** de subir. Skill `deploy-reproduzivel`.
> Data: AAAA-MM-DD · Responsável: <quem> · Autorização: <quem>

## 1. O que sobe

| Item | Valor |
|---|---|
| Versão | `vX.Y.Z` |
| Commit | `<sha>` |
| Artefato | `<imagem:tag ou pacote>` |
| Mudanças que importam | <uma linha; o resto está no CHANGELOG> |

## 2. Pré-condições

- [ ] CI verde **nesta revisão** (não numa anterior).
- [ ] Migração revisada e compatível para frente.
- [ ] Cópia de segurança do banco **verificada** (restaurada em teste, não só criada).
- [ ] Janela combinada com quem usa.

## 3. Passos

```bash
# comandos exatos, na ordem
```

## 4. Verificação — consultar o alvo, não acreditar no comando

```bash
curl -fsS https://<alvo>/health      # espera-se: 200 e as dependências "ok"
curl -fsS https://<alvo>/versao      # espera-se: vX.Y.Z — a que acabou de subir
```

- [ ] Versão respondida **é** a que subiu.
- [ ] `/health` confirma banco e dependências externas.
- [ ] Taxa de erro estável na janela de observação.

## 5. Rollback

```bash
# comando de volta
```

| Pergunta | Resposta |
|---|---|
| Tempo estimado | <minutos> |
| O que **não** desfaz | <migração aplicada, mensagem enviada, e-mail disparado, arquivo gravado> |
| Quem decide reverter | <papel> |

## 6. Depois

- Janela de observação: <15 min · 1 h> — declarada **antes**.
- Registro: subiu `<versão>` em `<data/hora>`, autorizado por `<quem>`, verificação `<ok|falhou>`.
- Reverteu? Motivo em uma linha e ticket aberto — rollback sem ticket vira o mesmo deploy na
  semana seguinte.
