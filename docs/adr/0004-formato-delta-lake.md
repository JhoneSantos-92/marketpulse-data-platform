# ADR-0004: Formato de tabela: Delta Lake

- **Status:** Aceito
- **Data:** 2026-09-25

## Contexto

As camadas bronze, silver e gold precisam de escrita confiável, deduplicação e histórico de versões.

## Decisão

Usar **Delta Lake** em todas as camadas.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| Delta Lake | ACID, time travel, MERGE; mesmo formato do Databricks | Nenhum relevante neste contexto |
| Apache Iceberg | Em alta no mercado | Exige um catálogo, mais um serviço |
| Parquet puro | O mais simples | Sem ACID e sem MERGE, deduplicação manual |

## Consequências

Aproxima o projeto do ecossistema Databricks, que faz parte da stack principal. MERGE resolve a deduplicação por `trade_id` na silver.
