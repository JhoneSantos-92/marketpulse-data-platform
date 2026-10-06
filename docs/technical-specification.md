# Especificação Técnica — MarketPulse Data Platform

**Versão:** 1.0.0  
**Status:** Concluído e Em Produção Local  
**Autor:** Jhone Estefano dos Santos  

---

## 1. Visão Geral do Sistema
O **MarketPulse Data Platform** é uma plataforma de engenharia de dados em tempo real projetada para ingestão, processamento, armazenamento, orquestração e entrega de métricas de mercado de criptoativos. A plataforma consome dados de trades e livro de ofertas (*book ticker*) da Binance, enriquece os dados com cotações oficiais do Banco Central do Brasil (USD/BRL) e consolida um modelo dimensional em estrela (*Star Schema*) para consumo em ferramentas de Business Intelligence (Power BI).

---

## 2. Stack Tecnológica e Versões

| Domínio | Tecnologia | Versão / Especificação | Propósito na Arquitetura |
|---|---|---|---|
| **Linguagem & Runtime** | Python | `>= 3.13` (CPython) | Linguagem principal de ingestão e transformação |
| **Gerenciamento de Pacotes** | `uv` | Última estável (`astral-sh/uv`) | Gerenciamento ultrarrápido de dependências e ambientes virtuais |
| **Mensageria (Streaming)** | Redpanda | `v26.2.3` (modo `dev-container`) | Broker compatível com API Kafka de alta performance |
| **Object Storage (S3)** | SeaweedFS | `4.47` | Armazenamento de objetos S3 autohosted |
| **Formato de Tabela (Lakehouse)** | Delta Lake (`delta-rs`) | `1.6.6` | Formato transacional ACID sobre arquivos Parquet |
| **Processamento de Dados** | Polars | `2.0.0` | Motor de processamento de dados colunar em Rust |
| **Orquestração** | Apache Airflow | `2.9.1` (`LocalExecutor`) | Orquestração de tarefas batch e pipelines horários |
| **Banco de Metadados (Airflow)** | PostgreSQL | `15-alpine` | Armazenamento de estado das DAGs do Airflow |
| **Qualidade & Testes** | `pytest` & `ruff` | `9.1.1` / `0.16.9` | Testes unitários e linter estrito de código |
| **CI/CD & Quality Gate** | GitHub Actions | Workflows integrados | Automação de linter, testes e branch protection |
| **Observabilidade & Alertas** | Prometheus, Grafana & WhatsApp API | Padrão da indústria | Monitoramento de métricas e alertas operacionais |

---

## 3. Arquitetura de Dados (Arquitetura Medalhão)

O fluxo de dados segue rigorosamente a arquitetura medalhão (*Medallion Architecture*):

```
[Binance WebSocket/REST] ──> [Redpanda (Kafka)] ──> [SeaweedFS (S3) - Bronze] 
                                                              │
                                                              v
[Power BI Dashboard] <── [SeaweedFS (S3) - Gold] <── [SeaweedFS (S3) - Silver]
```

### 3.1. Camada de Ingestão (`ingestion/` & `streaming/`)
- **Producer (`ingestion/producer.py`):** Conexão assíncrona com o WebSocket público da Binance (`wss://data-stream.binance.vision`) para os streams combinados `<symbol>@trade` e `<symbol>@bookTicker` (pares: BTCUSDT, ETHUSDT, SOLUSDT). Implementa reconexão com backoff exponencial e ping/pong a cada 20 segundos.
- **Backfill REST (`ingestion/backfill.py`):** Coleta de klines históricas (`GET /api/v3/klines`) na API REST da Binance (`https://data-api.binance.vision`) respeitando o peso das requisições e limites (*rate limit*).
- **Consumer (`streaming/consumer.py`):** Leitura assíncrona dos tópicos do Redpanda (`market.trades` e `market.book_ticker`) em lotes (*batching*) com *commit* manual de offsets (*at-least-once*).

### 3.2. Camada Bronze (`transformations/` - Bronze)
- **Armazenamento:** Salva os payloads JSON brutos "como vieram da origem" (*as-is*) acrescidos de metadados de controle (`ingestion_timestamp`, `kafka_offset`, `kafka_partition`).
- **Particionamento:** Organizado estritamente em `s3://marketpulse-lake/bronze/<tabela>/symbol=<par>/partition_date=<yyyy-mm-dd>/partition_hour=<hh>/`.

### 3.3. Camada Silver (`transformations/silver.py`)
- **Limpeza e Tipagem:** Conversão de strings decimais para tipos numéricos de alta precisão (Float64).
- **Deduplicação:** Eliminação de registros duplicados utilizando o ID único do trade (`trade_id` / `t`) (ADR-0004).
- **Enriquecimento Cambial:** Requisição diária à API do Banco Central do Brasil (SGS série 1) e *as-of join* temporal para conversão dos preços de USD para BRL (`price_brl`) (ADR-0012).
- **Cálculo de Spread:** Mensuração em tempo real do spread de mercado (`best_ask_price - best_bid_price`).
- **Armazenamento:** Gravado em `s3://marketpulse-lake/silver/` particionado por `symbol` e `partition_date`.

### 3.4. Camada Gold (`transformations/gold.py`)
- **Modelo Dimensional (Star Schema):**
  - **`fact_ohlcv_1m`:** Velas agregadas de 1 minuto contendo `open`, `high`, `low`, `close`, `volume` (em USD e BRL) e `trade_count`.
  - **`fact_market_metrics`:** Métricas diárias de liquidez e spread (`avg_spread`, `max_spread`, `min_spread`).
- **Armazenamento:** Gravado em `s3://marketpulse-lake/gold/`.

---

## 4. Infraestrutura e Orquestração

### 4.1. Docker Compose (`infra/docker-compose.yml`)
A infraestrutura local é orquestrada via Docker Compose, com portas restritas exclusivamente a `127.0.0.1` para segurança:
- **`redpanda`**: Porta `19092` (Kafka API) e `19644` (Admin).
- **`seaweedfs`**: Porta `8333` (Gateway S3 autenticado).
- **`airflow_postgres`**: Porta `5432` (Banco de metadados do Airflow).
- **`airflow`**: Porta `8080` (Web UI do Airflow rodando com `LocalExecutor`).

### 4.2. Orquestração (`orchestration/dags/market_pipeline_dag.py`)
- **Agendamento:** Execução horária automática (`schedule="@hourly"`).
- **Topologia de Tarefas:** `run_silver_layer >> run_gold_layer`. A camada Gold depende diretamente do sucesso da camada Silver.

---

## 5. Qualidade de Software e CI/CD

- **Testes Unitários (`tests/`):** Testes automatizados com `pytest` cobrindo URL builder, parsers de klines/BCB e carregamento de DAGs.
- **Linter Estrito (`ruff`):** Verificação rigorosa de estilo, imports e prevenção de exceções genéricas.
- **GitHub Actions (`.github/workflows/ci.yml`):** Pipeline de CI que executa `ruff check` e `pytest` em Python 3.13 a cada commit.
- **Branch Protection:** Configurado na branch `main` no GitHub para exigir aprovação obrigatória do status check do CI antes de permitir qualquer merge.

---

## 6. Guia de Execução Rápida

```bash
# 1. Configurar ambiente
cp .env.example .env

# 2. Subir infraestrutura
make up

# 3. Inicializar Lake (Criar bucket S3)
uv run python scripts/init_lake.py

# 4. Executar pipeline de ponta a ponta
uv run python ingestion/producer.py &
uv run python streaming/consumer.py &
uv run python transformations/silver.py
uv run python transformations/gold.py

# 5. Executar testes e linter
PYTHONPATH=. uv run pytest
uv run ruff check .
```
