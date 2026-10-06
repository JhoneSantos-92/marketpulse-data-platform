# Architecture Decision Records

Cada decisão técnica do projeto fica registrada em um arquivo, com contexto, opções e consequências.

| ADR | Decisão |
|---|---|
| [0001](0001-runtime-docker-wsl2.md) | Runtime: Docker Engine dentro do WSL2 |
| [0002](0002-mensageria-redpanda.md) | Mensageria: Redpanda |
| [0003](0003-object-storage-seaweedfs.md) | Object storage: SeaweedFS |
| [0004](0004-formato-delta-lake.md) | Formato de tabela: Delta Lake |
| [0005](0005-processamento-polars-delta-rs.md) | Processamento: Polars + delta-rs |
| [0006](0006-orquestracao-airflow-enxuto.md) | Orquestração: Airflow enxuto (LocalExecutor) |
| [0007](0007-qualidade-de-dados.md) | Qualidade de dados: checagens em Polars + pytest, testes dbt na gold |
| [0008](0008-observabilidade-e-custo.md) | Observabilidade e custo: Prometheus + Grafana + tabela de execuções |
| [0009](0009-alertas-telegram.md) | Alertas: bot do Telegram |
| [0010](0010-bi-power-bi.md) | BI: Power BI Desktop |
| [0011](0011-streams-binance.md) | Fontes da Binance: @trade + @bookTicker e REST para backfill |
| [0012](0012-conversao-usd-brl.md) | Conversão USD/BRL: última cotação disponível (série SGS 1) |
| [0013](0013-ambiente-python-uv.md) | Ambiente Python: uv com Python 3.13 |
