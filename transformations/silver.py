import json
import logging
import os
import sys
from datetime import UTC, datetime

import httpx
import polars as pl
from deltalake import DeltaTable, write_deltalake
from deltalake.exceptions import TableNotFoundError
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from monitoring.alert import send_whatsapp_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("silver_transformation")

def get_s3_storage_options() -> dict[str, str]:
    access_key = os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("S3_SECRET_KEY")
    if not access_key or not secret_key:
        raise OSError("S3_ACCESS_KEY and S3_SECRET_KEY must be set in environment.")
    return {
        "AWS_ACCESS_KEY_ID": access_key,
        "AWS_SECRET_ACCESS_KEY": secret_key,
        "AWS_ENDPOINT_URL": os.getenv("S3_ENDPOINT", "http://localhost:8333"),
        "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
        "AWS_ALLOW_HTTP": "true",
        "AWS_REGION": "us-east-1",
    }

def fetch_bcb_exchange_rates(bcb_url: str) -> pl.DataFrame:
    logger.info(f"Buscando cotações USD/BRL do Banco Central (SGS 1): {bcb_url}")
    try:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }
        response = httpx.get(bcb_url, headers=headers, timeout=30.0)
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
        err_msg = f"Aviso ao buscar cotações do BCB ({e}). Usando cotação padrão de fallback (5.50)."
        logger.warning(err_msg)
        send_whatsapp_alert(f"ALERTA: Falha ao buscar cotações do Banco Central (SGS 1): {e}. Cotação de fallback (5.50) ativada.")
        today_str = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        return pl.DataFrame({
            "exchange_date": [today_str],
            "usd_brl": [5.50]
        })

def transform_trades(storage_uri: str, storage_options: dict, df_bcb: pl.DataFrame) -> None:
    source_path = f"{storage_uri}/bronze/trades"
    dest_path = f"{storage_uri}/silver/trades"

    logger.info(f"Lendo camada Bronze de Trades: {source_path}")
    try:
        df_bronze = pl.read_delta(source_path, storage_options=storage_options)
    except (ValueError, FileNotFoundError, OSError, TableNotFoundError) as e:
        logger.warning(f"Tabela Bronze de Trades não encontrada ou vazia ({e}). Pulando transformação.")
        return

    if df_bronze.is_empty():
        logger.info("Nenhum dado encontrado na tabela Bronze de Trades.")
        return

    logger.info(f"Processando {len(df_bronze)} registros da Bronze de Trades.")

    valid_rows = []
    quarantine_rows = []
    current_ts = int(datetime.now(tz=UTC).timestamp() * 1000)

    for row in df_bronze.iter_rows(named=True):
        raw_json_str = row.get("raw_json", "{}")
        try:
            raw = json.loads(raw_json_str)
            trade_id = int(raw.get("t"))
            price = float(raw.get("p", 0.0))
            qty = float(raw.get("q", 0.0))
            ts = int(raw.get("T", row["ingestion_timestamp"]))

            rejection_reason = None
            if price <= 0:
                rejection_reason = "INVALID_PRICE_NON_POSITIVE"
            elif qty <= 0:
                rejection_reason = "INVALID_QUANTITY_NON_POSITIVE"
            elif ts <= 0:
                rejection_reason = "INVALID_TIMESTAMP_NON_POSITIVE"

            if rejection_reason:
                quarantine_rows.append({
                    "raw_json": raw_json_str,
                    "rejection_reason": rejection_reason,
                    "rejection_timestamp": current_ts,
                    "source_table": "bronze_trades",
                })
            else:
                valid_rows.append({
                    "trade_id": trade_id,
                    "symbol": raw.get("s", "").lower(),
                    "price": price,
                    "quantity": qty,
                    "trade_timestamp": ts,
                    "is_buyer_maker": bool(raw.get("m", False)),
                    "partition_date": row["partition_date"],
                    "partition_hour": row["partition_hour"],
                })
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            quarantine_rows.append({
                "raw_json": raw_json_str,
                "rejection_reason": f"PARSING_ERROR: {e!s}",
                "rejection_timestamp": current_ts,
                "source_table": "bronze_trades",
            })

    if quarantine_rows:
        q_path = f"{storage_uri}/silver/quarantine_trades"
        df_q = pl.DataFrame(quarantine_rows)
        logger.warning(f"Encontrados {len(quarantine_rows)} registros inválidos. Gravando na quarentena: {q_path}")
        try:
            write_deltalake(
                q_path,
                df_q.to_arrow(),
                mode="append",
                storage_options=storage_options,
            )
        except Exception as q_err:  # noqa: BLE001
            logger.error(f"Erro ao gravar na quarentena: {q_err}")

    if not valid_rows:
        logger.info("Nenhum registro válido de trade após validação.")
        return

    df_parsed = pl.DataFrame(valid_rows)

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
        df_joined = df_dedup.with_columns(pl.lit(5.50).alias("usd_brl"))

    df_silver = df_joined.with_columns(
        (pl.col("price") * pl.col("usd_brl")).alias("price_brl")
    )

    logger.info(f"Escrevendo/fazendo upsert da tabela Silver de Trades em {dest_path}")
    try:
        dt = DeltaTable(dest_path, storage_options=storage_options)
        dt.merge(
            source=df_silver.to_arrow(),
            predicate="target.trade_id = source.trade_id",
            source_alias="source",
            target_alias="target"
        ).when_matched_update_all().when_not_matched_insert_all().execute()
        logger.info(f"Merge (upsert) executado com sucesso na tabela Silver de Trades em {dest_path}")
    except (ValueError, FileNotFoundError, OSError, TableNotFoundError):
        write_deltalake(
            dest_path,
            df_silver.to_arrow(),
            mode="append",
            storage_options=storage_options,
            partition_by=["symbol", "partition_date"],
        )
        logger.info(f"Tabela Silver de Trades criada/escrita em {dest_path}")

def transform_book_ticker(storage_uri: str, storage_options: dict) -> None:
    source_path = f"{storage_uri}/bronze/book_ticker"
    dest_path = f"{storage_uri}/silver/book_ticker"

    logger.info(f"Lendo camada Bronze de BookTicker: {source_path}")
    try:
        df_bronze = pl.read_delta(source_path, storage_options=storage_options)
    except (ValueError, FileNotFoundError, OSError, TableNotFoundError) as e:
        logger.warning(f"Tabela Bronze de BookTicker não encontrada ou vazia ({e}). Pulando transformação.")
        return

    if df_bronze.is_empty():
        logger.info("Nenhum dado encontrado na tabela Bronze de BookTicker.")
        return

    logger.info(f"Processando {len(df_bronze)} registros da Bronze de BookTicker.")

    valid_rows = []
    quarantine_rows = []
    current_ts = int(datetime.now(tz=UTC).timestamp() * 1000)

    for row in df_bronze.iter_rows(named=True):
        raw_json_str = row.get("raw_json", "{}")
        try:
            raw = json.loads(raw_json_str)
            update_id = int(raw.get("u", 0))
            bid_price = float(raw.get("b", 0.0))
            ask_price = float(raw.get("a", 0.0))

            rejection_reason = None
            if bid_price < 0 or ask_price < 0:
                rejection_reason = "INVALID_BID_ASK_PRICE_NEGATIVE"

            if rejection_reason:
                quarantine_rows.append({
                    "raw_json": raw_json_str,
                    "rejection_reason": rejection_reason,
                    "rejection_timestamp": current_ts,
                    "source_table": "bronze_book_ticker",
                })
            else:
                valid_rows.append({
                    "update_id": update_id,
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
            quarantine_rows.append({
                "raw_json": raw_json_str,
                "rejection_reason": f"PARSING_ERROR: {e!s}",
                "rejection_timestamp": current_ts,
                "source_table": "bronze_book_ticker",
            })

    if quarantine_rows:
        q_path = f"{storage_uri}/silver/quarantine_book_ticker"
        df_q = pl.DataFrame(quarantine_rows)
        logger.warning(f"Encontrados {len(quarantine_rows)} registros inválidos de book_ticker. Gravando na quarentena: {q_path}")
        try:
            write_deltalake(
                q_path,
                df_q.to_arrow(),
                mode="append",
                storage_options=storage_options,
            )
        except Exception as q_err:  # noqa: BLE001
            logger.error(f"Erro ao gravar na quarentena de book_ticker: {q_err}")

    if not valid_rows:
        return

    df_silver = pl.DataFrame(valid_rows)

    logger.info(f"Escrevendo/fazendo upsert da tabela Silver de BookTicker em {dest_path}")
    try:
        dt = DeltaTable(dest_path, storage_options=storage_options)
        dt.merge(
            source=df_silver.to_arrow(),
            predicate="target.update_id = source.update_id",
            source_alias="source",
            target_alias="target"
        ).when_matched_update_all().when_not_matched_insert_all().execute()
        logger.info(f"Merge (upsert) executado com sucesso na tabela Silver de BookTicker em {dest_path}")
    except (ValueError, FileNotFoundError, OSError, TableNotFoundError):
        write_deltalake(
            dest_path,
            df_silver.to_arrow(),
            mode="append",
            storage_options=storage_options,
            partition_by=["symbol", "partition_date"],
        )
        logger.info(f"Tabela Silver de BookTicker criada/escrita em {dest_path}")

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
