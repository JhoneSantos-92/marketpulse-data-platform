# ADR-0011: Fontes da Binance: @trade + @bookTicker e REST para backfill

- **Status:** Aceito
- **Data:** 2026-09-25

## Contexto

O projeto precisa de dados em tempo real com identificador único (para deduplicar) e de preço de compra e venda (para calcular spread). Só endpoints públicos de market data podem ser usados.

## Decisão

Usar o endpoint somente de market data `wss://data-stream.binance.vision` com os streams **`<symbol>@trade`** e **`<symbol>@bookTicker`**, começando com 3 pares. O backfill histórico usa **`GET /api/v3/klines`** em `https://data-api.binance.vision` (peso 2, até 1000 velas por chamada). Regras da documentação oficial que o código deve respeitar: conexão cai em 24 horas, ping a cada 20 segundos com pong em até 1 minuto, limite de 5 mensagens recebidas por segundo por conexão, e respeitar o `Retry-After` em HTTP 429 para evitar bloqueio 418. O volume de `@bookTicker` será medido na Fase 1.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| @trade + @bookTicker | trade_id permite deduplicar; bookTicker dá o spread | Volume alto de mensagens |
| @aggTrade + @bookTicker | Menos mensagens | Agrega trades e perde a deduplicação por trade_id |
| Só @kline_1m | Muito leve | Deixa de ser tempo real |

## Consequências

Dados granulares e de verdade, com a responsabilidade de lidar com volume, reconexão e limites da API.
