Abaixo, um **trecho** do verificador do nosso painel de tickets. O painel é um Markdown com
seções `## Em aberto`, `## Concluídos` e `## Abandonados`, e cada linha começa com um marcador
(`[ ]`, `[>]`, `[!]`, `[x]`, `[~]`).

```python
SECAO_DE = {"em aberto": {" ", ">", "!"}, "concluídos": {"x"}, "abandonados": {"~"}}

for n, linha in enumerate(texto.splitlines(), 1):
    if linha.startswith("## "):
        secao = linha[3:].strip().lower()
        continue
    m = ITEM.match(linha)
    if not m:
        continue
    marcador = m.group(1)
    esperado = SECAO_DE.get(secao)
    if esperado and marcador not in esperado:
        problemas.append(f"linha {n}: marcador '[{marcador}]' fora da seção certa")
```

Escreva o corpo de um ticket de defeitos: liste o que este verificador deixa passar.
