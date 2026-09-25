# MarketPulse Data Platform

Plataforma de dados de mercado de criptoativos em tempo real. Consome trades e o livro de ofertas da Binance, converte os valores para reais com o câmbio oficial do Banco Central e entrega métricas prontas para BI, passando por todo o ciclo de engenharia de dados: ingestão, mensageria, arquitetura medalhão, orquestração, qualidade, observabilidade e custo.

> 🚧 Em construção. Este README é atualizado ao final de cada fase.

## Problema de negócio

<!-- Fase 8: qual pergunta de negócio o dashboard responde e para quem. -->

## Arquitetura

```mermaid
flowchart LR
    subgraph Fontes
        WS["Binance WebSocket<br/>@trade + @bookTicker"]
        REST["Binance REST<br/>GET /api/v3/klines"]
        BCB["BCB SGS série 1<br/>USD/BRL diário"]
    end

    subgraph ingestion
        PROD["Producer<br/>reconexão + backoff"]
        BF["Backfill<br/>respeita REQUEST_WEIGHT"]
    end

    subgraph streaming["Redpanda (API Kafka)"]
        T1[("market.trades<br/>key = symbol")]
        T2[("market.book_ticker")]
        DLQ[("market.dlq")]
    end

    CONS["Consumer group<br/>commit após escrita"]

    subgraph lake["SeaweedFS (S3) + Delta Lake"]
        BR["Bronze<br/>bruto + metadados<br/>symbol/date/hour"]
        SI["Silver<br/>tipado, dedup trade_id,<br/>preço em BRL"]
        GO["Gold<br/>star schema, OHLCV,<br/>volatilidade, spread"]
    end

    WS --> PROD --> T1 & T2
    REST --> BF --> T1
    T1 & T2 --> CONS --> BR
    CONS -. erro de parse .-> DLQ
    BR --> SI --> GO
    BCB --> SI
    GO --> BI["Power BI"]

    ORQ["Airflow"] -.agenda.-> BF & SI & GO
    MON["Prometheus + Grafana<br/>lag, throughput, latência, custo"] -.-> CONS & ORQ
    MON --> AL["Alerta Telegram"]
```

## Stack

| Camada | Ferramenta | Por quê |
|---|---|---|
| Runtime | Docker Engine no WSL2 | [ADR-0001](docs/adr/0001-runtime-docker-wsl2.md) |
| Mensageria | Redpanda | [ADR-0002](docs/adr/0002-mensageria-redpanda.md) |
| Object storage | SeaweedFS (S3) | [ADR-0003](docs/adr/0003-object-storage-seaweedfs.md) |
| Formato de tabela | Delta Lake | [ADR-0004](docs/adr/0004-formato-delta-lake.md) |
| Processamento | Polars + delta-rs | [ADR-0005](docs/adr/0005-processamento-polars-delta-rs.md) |
| Orquestração | Airflow (LocalExecutor) | [ADR-0006](docs/adr/0006-orquestracao-airflow-enxuto.md) |
| Qualidade | Polars + pytest | [ADR-0007](docs/adr/0007-qualidade-de-dados.md) |
| Observabilidade | Prometheus + Grafana | [ADR-0008](docs/adr/0008-observabilidade-e-custo.md) |
| Alertas | Telegram | [ADR-0009](docs/adr/0009-alertas-telegram.md) |
| BI | Power BI Desktop | [ADR-0010](docs/adr/0010-bi-power-bi.md) |

Todas as decisões estão em [docs/adr](docs/adr/README.md).

## Estrutura do repositório

| Pasta | Conteúdo |
|---|---|
| `ingestion/` | Producer WebSocket e backfill REST |
| `streaming/` | Consumer, tópicos e DLQ |
| `transformations/` | Bronze, silver e gold |
| `orchestration/` | DAGs do Airflow |
| `monitoring/` | Prometheus, Grafana e alertas |
| `tests/` | Testes automatizados |
| `infra/` | Docker Compose e configurações |
| `bi/` | Dashboard do Power BI |
| `docs/adr/` | Decisões de arquitetura |

## Como rodar

**Pré-requisitos:** Docker Engine com o plugin Compose (no Windows, dentro do WSL2; ver [ADR-0001](docs/adr/0001-runtime-docker-wsl2.md)), `make` e `openssl`.

```bash
cp .env.example .env
openssl rand -hex 16   # rode duas vezes: uma chave para S3_ACCESS_KEY, outra para S3_SECRET_KEY
make up                # sobe os serviços
make ps                # o redpanda deve aparecer como (healthy)
make stats             # consumo de CPU e RAM por container
make down              # derruba tudo (os dados ficam nos volumes)
```

| Serviço | Endereço local | Função |
|---|---|---|
| Redpanda | `localhost:19092` | Broker (API Kafka) |
| SeaweedFS | `http://localhost:8333` | Object storage (API S3, exige chave) |

Todas as portas escutam só em `127.0.0.1`.

**Consumo medido** (`docker stats`, serviços ociosos): Redpanda ~430 MiB, SeaweedFS ~70 MiB.

## Insights do dashboard

<!-- Fase 8: prints do BI. -->

## Aprendizados

<!-- Atualizado ao final de cada fase. -->
