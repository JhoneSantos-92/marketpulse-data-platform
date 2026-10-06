# MarketPulse BI Dashboard (Power BI Desktop)

Este diretório contém a documentação e as diretrizes de integração para o dashboard executivo do **MarketPulse Data Platform** construído no **Power BI Desktop** (conforme [ADR-0010](../docs/adr/0010-bi-power-bi.md)).

## 1. Pergunta de Negócio e Público-Alvo
- **Público-alvo:** Traders, analistas de mercado, tesouraria e gestores de risco em criptoativos.
- **Pergunta de Negócio:** *"Como o comportamento em tempo real de preço (em USD e BRL), volume negociado e volatilidade dos principais criptoativos (BTC, ETH, SOL) se correlaciona com o spread de liquidez do livro de ofertas e a variação cambial oficial?"*

## 2. Modelo de Dados (Star Schema)
O dashboard consome diretamente as tabelas consolidadas na **Camada Gold** armazenadas no SeaweedFS Delta Lake:
- **`fact_ohlcv_1m`**: Fato contendo velas de 1 minuto (Open, High, Low, Close, Volume) com preços em **USD** e **BRL** (convertidos via cotação oficial do Banco Central do Brasil - SGS 1).
- **`fact_market_metrics`**: Fato contendo métricas diárias de liquidez e spread (`avg_spread`, `max_spread`, `min_spread`).

## 3. Como Conectar o Power BI à Camada Gold
1. Abra o **Power BI Desktop** no Windows.
2. Utilize o conector **Delta Lake** ou **Amazon S3 / Spark / Python** para apontar para o storage S3 local:
   - Endpoint S3: `http://localhost:8333`
   - Bucket / Lake URI: `s3://marketpulse-lake/gold/`
3. Importe as tabelas `fact_ohlcv_1m` e `fact_market_metrics`.
4. Crie os relacionamentos por `symbol` e `partition_date`.

## 4. Principais Indicadores (KPIs) no Dashboard
- **Preço Atual vs. Variação 24h** (em BRL e USD).
- **Volume Total Negociado** por par de ativos.
- **Gráfico de Candlestick (OHLCV)** em Reais.
- **Evolução do Spread de Liquidez** ao longo do dia.
- **Impacto Cambial:** Comparação da volatilidade em dólar versus em reais.
