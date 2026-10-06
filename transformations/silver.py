import json
import logging
import os
import sys
from datetime import datetime

import httpx
import polars as pl
from deltalake import DeltaTable, write_deltalake
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("silver_transformation")

def get_s3_storage_options() -> dict[str, str]:
    return {
        "AWS_ACCESS_KEY_ID": os.getenv("S3_ACCESS_KEY", "admin"),
        "AWS_SECRET_ACCESS_KEY": os.getenv("S3_SECRET_KEY", "admin"),
        "AWS_ENDPOINT_URL": os.getenv("S3_ENDPOINT", "http://localhost:8333"),
        "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
    }

def fetch_bcb_exchange_rates(bcb_url: str) -> pl.DataFrame:
    logger.info(f"Buscando cotações USD/BRL do Banco Central (SGS 1): {bcb_url}")
    try:
        response = httpx.get(bcb_url, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        
        rows = []
        for item in data:
            date_raw = item.get("data")
            val_raw = item.get("valor")
            if date_raw and val_raw:
                dt = datetime.strptime(date_raw, "%d/%m/%Y")  # noqa: DTZ007
                rows.append({
                    "exchange_date": dt.strftime("%Y-%m-%d"),
                    "usd_brl": float(val_raw)
                })

        df_bcb = pl.DataFrame(rows).sort("exchange_date")
        logger.info(f"Total de {len(df_bcb)} cotações obtidas do BCB.")
        return df_bcb
    except (httpx.HTTPError, ValueError, KeyError) as e:
        logger.error(f"Erro ao buscar cotações do BCB: {e}")
        return pl.DataFrame(schema={"exchange_date": pl.String, "usd_brl": pl.Float64})

def transform_trades(storage_uri: str, storage_options: dict, df_bcb: pl.DataFrame) -> None:
    source_path = f"{storage_uri}/bronze/trades"
    dest_path = f"{storage_uri}/silver/trades"

    logger.info(f"Lendo camada Bronze de Trades: {source_path}")
    try:
        dt = DeltaTable(source_path, storage_options=storage_options)
        df_bronze = dt.to_polars()
    except (ValueError, FileNotFoundError, OSError) as e:
        logger.warning(f"Tabela Bronze de Trades não encontrada ou vazia ({e}). Pulando transformação.")
        return

    if df_bronze.is_empty():
        logger.info("Nenhum dado encontrado na tabela Bronze de Trades.")
        return

    logger.info(f"Processando {len(df_bronze)} registros da Bronze de Trades.")

    parsed_rows = []
    for row in df_bronze.iter_dicts():
        try:
            raw = json.loads(row["raw_json"])
            parsed_rows.append({
                "trade_id": int(raw.get("t")),
                "symbol": raw.get("s", "").lower(),
                "price": float(raw.get("p", 0.0)),
                "quantity": float(raw.get("q", 0.0)),
                "trade_timestamp": int(raw.get("T", row["ingestion_timestamp"])),
                "is_buyer_maker": bool(raw.get("m", False)),
                "partition_date": row["partition_date"],
                "partition_hour": row["partition_hour"],
            })
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.debug(f"Erro ao parsear trade: {e}")

    if not parsed_rows:
        return

    df_parsed = pl.DataFrame(parsed_rows)

    df_dedup = df_parsed.unique(subset=["trade_id"])
    logger.info(f"Registros após deduplicação por trade_id: {len(df_dedup)} (removidos {len(df_parsed) - len(df_dedup)} duplicados).")

    df_dedup = df_dedup.with_columns(
        pl.from_epoch("trade_timestamp", time_unit="ms").dt.date().cast(pl.String).alias("trade_date")
    )

    if not df_bcb.is_empty():
        df_joined = df_dedup.join(
            df_bcb,
            left_on="trade_date",
            right_on="exchange_date",
            how="left"
        ).with_columns(
            pl.col("usd_brl").forward_fill().backward_fill().alias("usd_brl")
        )
    else:
        df_joined = df_dedup.with_columns(pl.lit(1.0).alias("usd_brl"))

    df_silver = df_joined.with_columns(
        (pl.col("price") * pl.col("usd_brl")).alias("price_brl")
    )

    logger.info(f"Escrevendo tabela Silver de Trades em {dest_path}")
    write_deltalake(
        dest_path,
        df_silver.to_arrow(),
        mode="append",
        storage_options=storage_options,
        partition_by=["symbol", "partition_date"],
    )

def transform_book_ticker(storage_uri: str, storage_options: dict) -> None:
    source_path = f"{storage_uri}/bronze/book_ticker"
    dest_path = f"{storage_uri}/silver/book_ticker"

    logger.info(f"Lendo camada Bronze de BookTicker: {source_path}")
    try:
        dt = DeltaTable(source_path, storage_options=storage_options)
        df_bronze = dt.to_polars()
    except (ValueError, FileNotFoundError, OSError) as e:
        logger.warning(f"Tabela Bronze de BookTicker não encontrada ou vazia ({e}). Pulando transformação.")
        return

    if df_bronze.is_empty():
        logger.info("Nenhum dado encontrado na tabela Bronze de BookTicker.")
        return

    logger.info(f"Processando {len(df_bronze)} registros da Bronze de BookTicker.")

    parsed_rows = []
    for row in df_bronze.iter_dicts():
        try:
            raw = json.loads(row["raw_json"])
            bid_price = float(raw.get("b", 0.0))
            ask_price = float(raw.get("a", 0.0))
            parsed_rows.append({
                "update_id": int(raw.get("u", 0)),
                "symbol": raw.get("s", "").lower(),
                "best_bid_price": bid_price,
                "best_bid_qty": float(raw.get("B", 0.0)),
                "best_ask_price": ask_price,
                "best_ask_qty": float(raw.get("A", 0.0)),
                "spread": ask_price - bid_price,
                "partition_date": row["partition_date"],
                "partition_hour": row["partition_hour"],
            })
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.debug(f"Erro ao parsear book_ticker: {e}")

    if not parsed_rows:
        return

    df_silver = pl.DataFrame(parsed_rows)

    logger.info(f"Escrevendo tabela Silver de BookTicker em {dest_path}")
    write_deltalake(
        dest_path,
        df_silver.to_arrow(),
        mode="append",
        storage_options=storage_options,
        partition_by=["symbol", "partition_date"],
    )

def main() -> None:
    load_dotenv()

    storage_uri = os.getenv("STORAGE_URI", "s3://marketpulse-lake")
    bcb_url = os.getenv("BCB_SGS_URL", "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados?formato=json")
    storage_options = get_s3_storage_options()

    logger.info("Iniciando processamento da camada Silver...")

    df_bcb = fetch_bcb_exchange_rates(bcb_url)
    transform_trades(storage_uri, storage_options, df_bcb)
    transform_book_ticker(storage_uri, storage_options)

    logger.info("Camada Silver processada com sucesso!")

if __name__ == "__main__":
    main()
