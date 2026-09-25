# ADR-0005: Processamento: Polars + delta-rs

- **Status:** Aceito
- **Data:** 2026-09-25

## Contexto

Com 7,9 GB de RAM divididos entre broker, storage, orquestrador e monitoramento, um motor pesado como Spark local compromete a estabilidade de todo o ambiente.

## Decisão

Usar **Polars + delta-rs** nas camadas bronze e silver. Para a gold, o **dbt-duckdb** será avaliado na Fase 5 (testes e linhagem de graça), e esta ADR será atualizada com a decisão. PySpark fica para um projeto separado no Databricks Free Edition.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| PySpark local | Mesmo código do Databricks, muito pedido em vagas | JVM pesada para a máquina, risco de travar o ambiente |
| Polars + delta-rs | Leve, rápido, sem JVM | Menos citado em vagas do que Spark |
| dbt-duckdb | SQL, testes e documentação de linhagem | Escrita nativa em Delta não é garantida; precisa verificar na documentação do adapter |

## Consequências

O ambiente fica estável na máquina disponível. A relevância de mercado do Spark é coberta em outro projeto.
