import logging
import os
import sys

import polars as pl
from deltalake import DeltaTable, write_deltalake
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("gold_transformation")

def get_s3_storage_options() -> dict[str, str]:
    return {
        "AWS_ACCESS_KEY_ID": os.getenv("S3_ACCESS_KEY", "admin"),
        "AWS_SECRET_ACCESS_KEY": os.getenv("S3_SECRET_KEY", "admin"),
        "AWS_ENDPOINT_URL": os.getenv("S3_ENDPOINT", "http://localhost:8333"),
        "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
    }

def transform_gold_ohlcv(storage_uri: str, storage_options: dict) -> None:
    source_path = f"{storage_uri}/silver/trades"
    dest_path = f"{storage_uri}/gold/fact_ohlcv_1m"

    logger.info(f"Lendo camada Silver de Trades: {source_path}")
    try:
        dt = DeltaTable(source_path, storage_options=storage_options)
        df_silver = dt.to_polars()
    except (ValueError, FileNotFoundError, OSError) as e:
        logger.warning(f"Tabela Silver de Trades não encontrada ou vazia ({e}). Pulando agregação Gold.")
        return

    if df_silver.is_empty():
        logger.info("Nenhum dado encontrado na tabela Silver de Trades.")
        return

    logger.info(f"Gerando OHLCV 1m para {len(df_silver)} registros da Silver.")

    # Converte timestamp para datetime do Polars
    df_transformed = df_silver.with_columns(
        pl.from_epoch("trade_timestamp", time_unit="ms").alias("trade_dt")
    )

    # Agregação OHLCV por símbolo em janelas de 1 minuto
    df_ohlcv = (
        df_transformed.group_by_dynamic(
            "trade_dt",
            every="1m",
            group_by="symbol",
        )
        .agg([
            pl.col("price").first().alias("open"),
            pl.col("price").max().alias("high"),
            pl.col("price").min().alias("low"),
            pl.col("price").last().alias("close"),
            pl.col("quantity").sum().alias("volume"),
            pl.col("price_brl").first().alias("open_brl"),
            pl.col("price_brl").max().alias("high_brl"),
            pl.col("price_brl").min().alias("low_brl"),
            pl.col("price_brl").last().alias("close_brl"),
            pl.count("trade_id").alias("trade_count"),
        ])
        .sort(["symbol", "trade_dt"])
    )

    logger.info(f"Escrevendo fato OHLCV Gold em {dest_path}")
    write_deltalake(
        dest_path,
        df_ohlcv.to_arrow(),
        mode="append",
        storage_options=storage_options,
        partition_by=["symbol"],
    )

def transform_gold_metrics(storage_uri: str, storage_options: dict) -> None:
    source_path = f"{storage_uri}/silver/book_ticker"
    dest_path = f"{storage_uri}/gold/fact_market_metrics"

    logger.info(f"Lendo camada Silver de BookTicker: {source_path}")
    try:
        dt = DeltaTable(source_path, storage_options=storage_options)
        df_silver = dt.to_polars()
    except (ValueError, FileNotFoundError, OSError) as e:
        logger.warning(f"Tabela Silver de BookTicker não encontrada ou vazia ({e}). Pulando agregação Gold.")
        return

    if df_silver.is_empty():
        logger.info("Nenhum dado encontrado na tabela Silver de BookTicker.")
        return

    logger.info(f"Calculando métricas de spread para {len(df_silver)} registros da Silver BookTicker.")

    df_metrics = (
        df_silver.group_by(["symbol", "partition_date"])
        .agg([
            pl.col("spread").mean().alias("avg_spread"),
            pl.col("spread").max().alias("max_spread"),
            pl.col("spread").min().alias("min_spread"),
            pl.col("best_bid_price").mean().alias("avg_bid_price"),
            pl.col("best_ask_price").mean().alias("avg_ask_price"),
            pl.count("update_id").alias("ticker_count"),
        ])
    )

    logger.info(f"Escrevendo fatos de métricas Gold em {dest_path}")
    write_deltalake(
        dest_path,
        df_metrics.to_arrow(),
        mode="append",
        storage_options=storage_options,
        partition_by=["symbol", "partition_date"],
    )

def main() -> None:
    load_dotenv()

    storage_uri = os.getenv("STORAGE_URI", "s3://marketpulse-lake")
    storage_options = get_s3_storage_options()

    logger.info("Iniciando processamento da camada Gold (Star Schema & OHLCV)...")

    transform_gold_ohlcv(storage_uri, storage_options)
    transform_gold_metrics(storage_uri, storage_options)

    logger.info("Camada Gold processada com sucesso!")

if __name__ == "__main__":
    main()
