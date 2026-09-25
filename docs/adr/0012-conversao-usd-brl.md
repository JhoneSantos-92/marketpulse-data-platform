# ADR-0012: Conversão USD/BRL: última cotação disponível (série SGS 1)

- **Status:** Aceito
- **Data:** 2026-09-25

## Contexto

Cripto negocia 24 horas por dia, 7 dias por semana. A série 1 do SGS do Banco Central (dólar, taxa livre, venda) só tem valor em dias úteis.

## Decisão

Converter cada trade usando a **última cotação disponível** até a data do trade (as-of join). A fonte é `https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados?formato=json`. A data da cotação usada fica gravada na silver, para deixar claro quando a conversão usou a cotação de um dia anterior.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| Última cotação disponível | Padrão financeiro, todo trade é convertido | No fim de semana usa a cotação de sexta |
| Converter só em dias úteis | Mais puro | Buracos no BI |
| Par USDTBRL da Binance | Tempo real | Não é câmbio oficial e perde a integração com o BCB |

## Consequências

Toda linha da silver tem valor em BRL, com rastreabilidade de qual cotação foi usada.
