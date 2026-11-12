---
name: transcrever-video
description: >-
  Obtém a transcrição de um vídeo online pelo caminho barato — a legenda que a
  plataforma já tem — convertendo-a em texto corrido com yt-dlp, sem baixar o
  vídeo, sem ffmpeg e sem modelo de fala. Sem legenda — o caso comum em
  Facebook, Instagram, TikTok e áudio de WhatsApp —, traz o caminho caro: ASR
  local com Whisper, ainda sem ffmpeg. Aciona ao pedir "transcreva este
  vídeo", ao usar vídeo como fonte de pesquisa, ou quando a leitura direta da
  página do YouTube falhar por bloqueio.
---

# transcrever-video — a legenda primeiro, o modelo de fala só se precisar

Transcrever costuma ser tratado como problema de reconhecimento de fala: baixar o áudio,
instalar `ffmpeg`, puxar alguns gigabytes de modelo, esperar. Na maioria dos vídeos isso é
desnecessário — **a transcrição já existe** e é entregue em segundos.

## O princípio

> A plataforma já transcreveu. Só pague por ASR quando ela não tiver feito isso.

Ordem de preferência, e o motivo de cada degrau:

| Degrau | Custo | Quando |
|---|---|---|
| Legenda **manual** do autor | segundos | Sempre que existir — é revisada por gente |
| Legenda **automática** | segundos | Padrão na prática; boa para conteúdo falado |
| **ASR local** (Whisper e afins) | minutos + GB | Só sem legenda, ou quando a precisão do termo técnico decide |

## Uso

```bash
S=skills/dominio/transcrever-video/scripts
python3 -m venv .cache/transcricoes/.venv
.cache/transcricoes/.venv/bin/pip install -q yt-dlp      # uma vez

$S/legendas.py "https://youtu.be/<id>"                   # idioma original do vídeo
$S/legendas.py "<url>" --idiomas pt,en                   # preferência de idioma
$S/legendas.py "<url>" --manter-tempos                   # guarda também o .vtt com carimbos
```

Saída em `.cache/transcricoes/` (repo-local, ADR 0011 — acrescente `.cache/` ao `.gitignore`):
`<id>.txt` com o texto corrido e `<id>.meta` com título, canal, duração, idioma e **origem da
legenda** (manual ou automática). Sem legenda, o script sai com código `3` e diz isso.

## O que o script resolve e você não deveria reescrever

- **A duplicação da legenda automática.** Ela reemite a última linha junto com a próxima, para
  simular rolagem na tela. Concatenação ingênua produz um texto com quase tudo em dobro.
- **Marcação embutida** (`<c>`, `<00:00:01.000>`), entidades HTML e carimbos de tempo.
- **Preferência de idioma** com o original do vídeo como padrão — legenda traduzida
  automaticamente é tradução de máquina sobre transcrição de máquina, dois erros empilhados.

## Limites que importam para o uso como fonte

- **Legenda automática erra nome próprio, sigla e termo técnico**, e não tem pontuação
  confiável. Serve para entender o argumento; **não** cite número ou nome a partir dela sem
  conferir no vídeo.
- **Não há falantes identificados.** Em entrevista, quem disse o quê se perde — o texto vira um
  fluxo só. Se a atribuição importa, confira o trecho.
- **Vídeo sem fala** (demonstração silenciosa, código na tela) não tem transcrição útil: o que
  importa está na imagem.

## Quando não há legenda: o caminho caro

É o caso **comum** em Facebook, Instagram, TikTok e áudio de WhatsApp — as plataformas
sociais raramente expõem legenda. Aí vale baixar só o áudio e rodar ASR local:

```bash
S=skills/dominio/transcrever-video/scripts
uv run --no-project --with faster-whisper --with yt-dlp \
    --with nvidia-cublas-cu12 --with "nvidia-cudnn-cu12==9.*" \
    python $S/asr-local.py "<url-ou-arquivo>"           # sem GPU: omita os --with nvidia-*
```

- **Sem `ffmpeg` no sistema**: o áudio é decodificado pelo PyAV, que traz as próprias libs.
- **GPU se houver**: `large-v3-turbo` em float16 transcreve 9 min em ~20 s numa RTX 3070
  (8 GB). Sem GPU, cai para `small` em CPU e **declara** isso na 1ª linha do `.txt`.
- Entrada pode ser URL (yt-dlp baixa só o áudio) ou arquivo local (áudio de WhatsApp
  exportado, `.ogg`/`.opus`/`.m4a`).
- Post que exige login (Instagram, às vezes Facebook): baixe o arquivo pelo navegador e passe
  o caminho — evite `--cookies-from-browser`, que entrega a sessão inteira da pessoa ao script.

Rode local: mandar áudio para serviço externo é o caso que a `meeting-minutes` trata como
exfiltração do material mais sensível de um projeto.

## Ligação com o resto do acervo

`meeting-minutes` cuida de áudio **confidencial** e da ATA — este é o caso oposto, material
público usado como referência. `dominio/docling-local` faz o equivalente para PDF, inclusive a
disciplina de declarar procedência e não citar o que não foi conferido.

## Definição de pronto da skill

- [ ] A origem da legenda (manual, automática ou ASR) está registrada junto da transcrição.
- [ ] Nenhum número, nome próprio ou citação literal foi usado sem conferência no vídeo.
- [ ] Texto e metadados ficaram em `.cache/` repo-local, fora do controle de versão.
- [ ] Áudio confidencial não foi enviado a serviço externo.
