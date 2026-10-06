# Arquitetura e Fluxogramas do Sistema — MarketPulse Data Platform

Este documento apresenta os diagramas de arquitetura, fluxogramas de dados e topologia de componentes da **MarketPulse Data Platform**, estruturados sob os padrões de engenharia de dados de empresas globais de tecnologia.

---

## 1. Visão Geral da Arquitetura de Sistemas

O diagrama abaixo ilustra o ecossistema completo da plataforma, desde as fontes externas até o consumo final no BI, isolando as camadas de infraestrutura, mensageria, armazenamento e orquestração.

```mermaid
graph TB
    subgraph External Sources ["Fontes Externas"]
        WSS["Binance WebSocket<br/>(@trade & @bookTicker)"]
        REST["Binance REST API<br/>(GET /api/v3/klines)"]
        BCB["Banco Central do Brasil<br/>(SGS Série 1 - USD/BRL)"]
    end

    subgraph Ingestion Layer ["Camada de Ingestão & Streaming"]
        PROD["Async WebSocket Producer<br/>(ingestion/producer.py)"]
        BF["REST Backfill Script<br/>(ingestion/backfill.py)"]
        CONS["Kafka Consumer Group<br/>(streaming/consumer.py)"]
    end

    subgraph Messaging Broker ["Mensageria (Redpanda)"]
        T1[("market.trades")]
        T2[("market.book_ticker")]
        DLQ[("market.dlq")]
    end

    subgraph Lakehouse Storage ["Storage Object (SeaweedFS S3) + Delta Lake"]
        BRZ[("Bronze Layer<br/>(Raw JSON + Metadata)")]
        SLV[("Silver Layer<br/>(Cleaned, Deduped & BRL Enriched)")]
        GLD[("Gold Layer<br/>(Star Schema - OHLCV & Spread)")]
    end

    subgraph Orchestration ["Orquestração (Apache Airflow)"]
        DAG["Airflow DAG<br/>(marketpulse_transformation_pipeline)"]
    end

    subgraph Consumption ["Consumo & Observabilidade"]
        BI["Power BI Desktop<br/>(Direct Lake / Delta Lake)"]
        PROM["Prometheus & Grafana"]
        ALRT["WhatsApp Alerter<br/>(monitoring/alert.py)"]
    end

    %% Fluxos
    WSS --> PROD
    REST --> BF
    PROD --> T1 & T2
    BF --> T1
    T1 & T2 --> CONS
    CONS -. Falha de Parse .-> DLQ
    CONS --> BRZ

    DAG -->|Task 1: Hourly| SLV
    DAG -->|Task 2: Hourly| GLD
    BRZ --> SLV
    BCB --> SLV
    SLV --> GLD
    GLD --> BI

    PROM --> CONS & DAG
    DAG -. Erro no Pipeline .-> ALRT
```

---

## 2. Fluxograma da Arquitetura Medalhão

O detalhamento de como os dados evoluem e são transformados de ponta a ponta:

```mermaid
sequenceDiagram
    autonumber
    participant Binance as Binance API
    participant Producer as Ingestion Producer
    participant Redpanda as Redpanda (Kafka)
    participant Consumer as Streaming Consumer
    participant Bronze as Bronze Delta Lake (S3)
    participant Silver as Silver Delta Lake (S3)
    participant Gold as Gold Delta Lake (S3)
    participant BI as Power BI

    Note over Binance, Producer: Tempo Real (Streaming Contínuo)
    Binance->>Producer: WebSocket Stream (@trade / @bookTicker)
    Producer->>Redpanda: Publica eventos (Particionado por Symbol)
    Redpanda->>Consumer: Consome mensagens em lotes (Batch)
    Consumer->>Bronze: Grava dados brutos (as-is) + partição (symbol/date/hour)

    Note over Airflow, Gold: Orquestração Batch Horária (Airflow)
    Silver->>Bronze: Lê dados brutos
    Note over Silver: Deduplicação por trade_id & As-Of Join com cotação BCB (BRL)
    Silver->>Silver: Grava tabela limpa e tipada
    Gold->>Silver: Lê dados limpos da Silver
    Note over Gold: Agregação OHLCV 1m & Métricas de Spread (Star Schema)
    Gold->>Gold: Grava tabelas fato consolidadas
    BI->>Gold: Consulta direta para visualização executiva
```

---

## 3. Topologia das Tarefas no Apache Airflow

As dependências e o fluxo de execução horária gerenciados pelo Airflow (`LocalExecutor`):

```mermaid
flowchart LR
    Start([Início do Agendamento @hourly]) --> SilverTask[Task 1: run_silver_layer<br/>transformations/silver.py]
    SilverTask -->|Sucesso| GoldTask[Task 2: run_gold_layer<br/>transformations/gold.py]
    GoldTask -->|Sucesso| End([Pipeline Concluído com Sucesso])

    SilverTask -.->|Falha| Alert[Disparo de Alerta via WhatsApp]
    GoldTask -.->|Falha| Alert
```

---

## 4. Diagrama de Estados do Pipeline CI/CD (Quality Gate)

O fluxo de controle de qualidade e branches no GitHub:

```mermaid
stateDiagram-v2
    [*] --> FeatureBranch: Desenvolve na branch dev
    FeatureBranch --> PR: Abre Pull Request para main
    state CI <<fork>>
        PR --> CI: Dispara GitHub Actions (CI Quality Gate)
        CI --> Ruff: Executa linter (ruff check .)
        CI --> Pytest: Executa testes unitários (PYTHONPATH=. pytest)
    Ruff --> CheckFailed: Erro de estilo / imports
    Pytest --> CheckFailed: Teste quebrado
    Ruff --> CheckPassed: Sucesso
    Pytest --> CheckPassed: Sucesso
    CheckFailed --> [*]: Bloqueia Merge (Branch Protection)
    CheckPassed --> Merge: Aprova e realiza Merge na main
    Merge --> [*]
