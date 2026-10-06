import argparse
import json
import logging
import os
import sys
import time

import httpx
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("binance_backfill")

KLINE_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_asset_volume",
    "number_of_trades",
    "taker_buy_base_asset_volume",
    "taker_buy_quote_asset_volume",
    "ignore",
]

def fetch_klines(
    client: httpx.Client,
    base_url: str,
    symbol: str,
    interval: str = "1m",
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 1000,
) -> list[list]:
    url = f"{base_url}/api/v3/klines"
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit,
    }
    if start_time:
        params["startTime"] = start_time
    if end_time:
        params["endTime"] = end_time

    response = client.get(url, params=params, timeout=30.0)
    
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        logger.warning(f"Rate limit atingido (429). Aguardando {retry_after} segundos...")
        time.sleep(retry_after)
        return fetch_klines(client, base_url, symbol, interval, start_time, end_time, limit)

    response.raise_for_status()
    return response.json()

def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Binance REST API Backfill for Klines")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol (e.g., BTCUSDT)")
    parser.add_argument("--interval", type=str, default="1m", help="Kline interval (e.g., 1m, 1h)")
    parser.add_argument("--limit", type=int, default=10, help="Number of klines to fetch (max 1000)")
    args = parser.parse_args()

    base_url = os.getenv("BINANCE_REST_URL", "https://data-api.binance.vision")
    symbol = args.symbol.upper()

    logger.info(f"Iniciando backfill para {symbol} (intervalo: {args.interval}, limite: {args.limit})")
    logger.info(f"Endpoint REST: {base_url}")

    with httpx.Client() as client:
        try:
            raw_klines = fetch_klines(
                client=client,
                base_url=base_url,
                symbol=symbol,
                interval=args.interval,
                limit=args.limit,
            )

            logger.info(f"Total de {len(raw_klines)} registros obtidos com sucesso.")
            
            for kline in raw_klines[:5]:  # Exibe os primeiros 5 registros como amostra
                record = dict(zip(KLINE_COLUMNS, kline, strict=False))
                logger.info(json.dumps(record, ensure_ascii=False))

        except (httpx.HTTPError, ValueError, KeyError) as e:
            logger.error(f"Erro durante a execução do backfill: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
