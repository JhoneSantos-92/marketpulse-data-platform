
import asyncio
import json
import os

from dotenv import load_dotenv
from websockets.asyncio.client import connect

MAX_MESSAGES = 20

def build_url(base_url: str, symbol: str) -> str:
    streams = f"{symbol}@trade/{symbol}@bookTicker"
    return f"{base_url}/stream?streams={streams}"

async def main() -> None:
    load_dotenv()

    base_url = os.getenv("BINANCE_WS_URL")
    if not base_url:
        raise SystemExit("BINANCE_WS_URL não definido no .env")

    symbol = os.getenv("SYMBOLS", "btcusdt").split(",")[0].strip().lower()

    url = build_url(base_url, symbol)
    print(f"Conectando em: {url}\n")

    async with connect(url) as ws:
        count = 0
        async for message in ws:
            envelope = json.loads(message)
            print(envelope["stream"], envelope["data"])

            count += 1
            if count >= MAX_MESSAGES:
                break

if __name__ == "__main__":
    asyncio.run(main())
