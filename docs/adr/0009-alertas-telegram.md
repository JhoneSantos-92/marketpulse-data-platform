# ADR-0009: Alertas: bot do Telegram

- **Status:** Aceito
- **Data:** 2026-09-25

## Contexto

Falhas precisam avisar na hora, com o motivo, sem depender de alguém olhando o painel.

## Decisão

Usar um **bot do Telegram**. O token e o chat_id ficam no `.env`, nunca no Git.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| Telegram | Chega no celular, API de bot simples | Precisa criar o bot no BotFather |
| Discord (webhook) | Só uma URL | Menos usado no dia a dia |

## Consequências

O pipeline é "dedo duro": quebrou, avisa no celular.
