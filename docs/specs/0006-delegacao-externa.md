<!-- Caminho relativo: docs/specs/0006-delegacao-externa.md -->

# Spec 0006 — Delegação a modelo externo: um cliente, modelo medido, roteamento validado

- **Status:** Rascunho — **uma decisão pendente** (ver fim); criticada em contexto limpo em
  2026-10-29, achados incorporados
- **Data:** 2026-10-29
- **Decide a partir de:** ADR 0007 (delegação por perfil); ADR 0010 (delegação a gateway
  LiteLLM); ADR 0011 (estado de skill é repo-local)
- **Tickets:** [MT-33](../tickets/MT-33.md) (cliente único) → [MT-34](../tickets/MT-34.md)
  (sonda de capacidade) · [MT-35](../tickets/MT-35.md) (roteamento das skills de delegação)

## Problema

Delegar a um modelo externo falha de três jeitos, todos observados:

- **Cliente duplicado.** Três clientes faziam a mesma chamada a endpoint OpenAI-compatible, e um
  deles foi escrito do zero, em 2026-10-07, por não se ter achado o primeiro.
- **Modelo adivinhado pelo nome.** `--models` devolve identificadores e nada mais. O agente não
  sabe qual modelo raciocina, qual tem janela grande, qual aceita ferramenta. Em 2026-10-07
  foram duas correções de orçamento até a resposta sair. E desligar o raciocínio depende de
  quem serve o modelo: em 2026-10-29, o mesmo pedido ao GLM-5.3 teve o `--no-think` ignorado
  e, numa das chaves, **o raciocínio vazou para o conteúdo com código 0**.
- **Skill não encontrada.** Seis skills tratam de delegação, cada uma num eixo. O autor não
  lembrava quantas eram, e o agente não achou a que importava.

## Solução

O `oa-chat` é o único cliente. Uma sonda mede o modelo e grava o resultado em cache datado, e a
escolha de modelo para uma tarefa cita a medição, não um nome. Uma tabela "preciso de → ler"
roteia as seis skills, e um validador no CI impede que ela apodreça.

**Já entregue em 2026-10-29**, como primeira fatia do MT-34, com autoteste no CI: `--no-think`
manda as duas chaves conhecidas, recua sozinho da chave que o endpoint recusar, e
`--sonda-think` classifica em 12 chamadas se o raciocínio desliga, continua, vaza, estoura ou é
recusado.

## Histórias

1. **Como agente**, quero um cliente só, para não reescrevê-lo quando não o acho.
2. **Como agente**, quero saber, medido, o que um modelo faz antes de mandar trabalho para ele.
3. **Como agente**, quero que o `--no-think` desligue o raciocínio onde for possível, e uma
   sonda que me diga antes, por endpoint e modelo, se ele desliga, continua ou vaza o
   pensamento para a resposta. Numa chamada comum, o cliente não tem como distinguir
   raciocínio vazado de resposta; a sonda tem, porque conhece a resposta certa.
4. **Como mantenedor**, quero que nenhum nome de modelo more no corpo da skill.
5. **Como agente**, quero achar a skill de delegação certa pela pergunta que tenho.

## Decisões de implementação

| Decisão | Escolha | Onde |
|---|---|---|
| Cliente | `oa-chat`; cliente novo é regressão | MT-33 |
| Credencial | nunca em argv nem no disco pelo cliente | skill `delegacao-openai-compat` |
| Desligar raciocínio | as duas chaves conhecidas, recuo da recusada, `--extra` nunca retirado | entregue em 2026-10-29 |
| Cache da sonda | repo-local, fora do git; chave = endpoint + modelo; validade padrão de 30 dias, configurável | ADR 0011, MT-34 |
| `--sonda-think` × `--probe` | `--probe` inclui a medição da `--sonda-think` e a grava no cache; a `--sonda-think` continua avulsa e não grava | esta spec |
| Nome de modelo | só em ilha do usuário, datado; nunca no corpo da skill | MT-34 |
| Escolha ambígua | pergunta, não escolhe em silêncio | MT-34 |
| Skills de delegação | roteirizar, não fundir | MT-35; a redundância real é o MT-37 |

## Critérios de aceite

| # | Critério | Prova | Ticket |
|---|---|---|---|
| 1 | A árvore DEVE ter um único implementador de chamada HTTP a `/chat/completions` | `git grep -l 'chat/completions'` lista só o `oa-chat` e documentação | MT-33 |
| 2 | QUANDO `--no-think` é passado, a **primeira** tentativa DEVE enviar `chat_template_kwargs.enable_thinking=false` e `thinking.type=disabled`; sem `--no-think`, NÃO DEVE enviar nenhuma das duas | `testar-oa-chat.sh`, casos 1 e 6 — entregue | MT-34 |
| 3 | SE o endpoint responde 4xx nomeando uma chave que o `--no-think` pôs, ENTÃO o `oa-chat` DEVE repetir a chamada sem ela, mantendo a outra, e avisar em stderr; SE a chave veio de `--extra`, ou SE o 4xx não nomeia chave do `--no-think`, ENTÃO NÃO DEVE repetir | `testar-oa-chat.sh`, casos 2 a 4 — entregue | MT-34 |
| 4 | QUANDO `--sonda-think -m <modelo>` roda, o `oa-chat` DEVE fazer três chamadas em cada uma de quatro configurações (padrão, template, thinking, `--no-think`), classificar cada uma em desligou, pensou, vazou, estourou ou recusou, e recomendar a que desligou 3 em 3 — preferindo `--no-think` — ou dizer que nenhuma serve | `testar-oa-chat.sh`, casos 7 a 9 — entregue; medido em quatro modelos reais | MT-34 |
| 5 | QUANDO `--probe <modelo>` roda, o `oa-chat` DEVE gravar janela de contexto, se emite raciocínio, se honra desligar, se aceita ferramenta e latência, num cache datado | endpoint fabricado com comportamento conhecido, como o do `testar-oa-chat.sh`; os cinco campos batem com o esperado | MT-34 |
| 6 | ENQUANTO a medição está dentro da validade, uma nova sonda do mesmo modelo DEVE usar o cache | segunda execução sem chamada de rede | MT-34 |
| 7 | QUANDO se pede modelo para uma tarefa, o subcomando de escolha DEVE imprimir tarefa → critério → modelo medido, citando o cache; SE a escolha for ambígua, ENTÃO DEVE perguntar | execução com cache fabricado de dois modelos empatados | MT-34 |
| 8 | Toda linha da tabela "preciso de → ler" DEVE apontar para skill existente, e toda skill de delegação DEVE aparecer na tabela | validador no CI sai 0 | MT-35 |
| 9 | Cada uma das seis descrições de delegação DEVE dizer, em "NÃO use para", qual das outras cobre o caso vizinho | validador do MT-35 | MT-35 |

## Fora de escopo

- **Decidir qual modelo usar para quê.** Sai da medição, não da spec.
- **Fundir skills de delegação.** MT-37.
- **Delegação a modelo local** (perímetro de dado sensível): skill `delegacao-a-subagentes`,
  sem mudança aqui.

## Decisões pendentes

**E. O script pessoal fora de controle de versão.**
O MT-33 deixa em aberto apagá-lo ou reduzi-lo a um invólucro que chama o `oa-chat`. Ele é
seu e não está no repositório, então a decisão é sua. Recomendação: **invólucro de poucas
linhas**, que fixa o endereço e o modelo de preferência como variável de ambiente e delega ao
`oa-chat`. Mantém o atalho e acaba com o segundo cliente.
