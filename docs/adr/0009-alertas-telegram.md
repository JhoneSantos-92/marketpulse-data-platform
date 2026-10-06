# ADR-0009: Alertas: WhatsApp Business API

- **Status:** Aceito (atualizado)
- **Data:** 2026-09-25 (atualizado em 2026-10-06)

## Contexto

Falphas e gargalos críticos no pipeline precisam avisar a equipe na hora, com o motivo, sem depender de alguém olhando o painel, utilizando canais de mensageria instantânea usuais no dia a dia.

## Decisão

Usar a **WhatsApp Business API** para envio de alertas automatizados. As credenciais (`WHATSAPP_API_URL`, `WHATSAPP_TOKEN`, `WHATSAPP_TO`) ficam armazenadas exclusivamente no arquivo `.env`, nunca no Git.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| WhatsApp Business API | Canal de maior engajamento no Brasil, entrega direta no celular | Configuração da Meta Business ligeiramente mais burocrática que Telegram |
| Telegram Bot | Muito simples de configurar via BotFather | Menos utilizado comercialmente no Brasil para alertas de sistemas |
| Discord Webhook | URL simples | Menos adequado para alertas críticos fora de comunidades de TI |

## Consequências

O pipeline permanece vigilante ("dedo duro"): qualquer falha crítica na ingestão ou nas camadas dispara uma mensagem imediata via WhatsApp.
