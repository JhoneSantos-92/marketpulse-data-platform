import asyncio
import json
import logging
import os
import sys

from confluent_kafka import Producer
from dotenv import load_dotenv
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, WebSocketException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("binance_producer")

def build_combined_stream_url(base_url: str, symbols: list[str]) -> str:
    streams = []
    for symbol in symbols:
        s = symbol.strip().lower()
        streams.append(f"{s}@trade")
        streams.append(f"{s}@bookTicker")
    combined = "/".join(streams)
    return f"{base_url}/stream?streams={combined}"

def delivery_report(err, msg):
    if err is not None:
        logger.error(f"Erro ao entregar mensagem no tópico {msg.topic()}: {err}")
    else:
        logger.debug(f"Mensagem entregue em {msg.topic()} [partição {msg.partition()}]")

async def main() -> None:
    load_dotenv()

    base_url = os.getenv("BINANCE_WS_URL", "wss://data-stream.binance.vision")
    raw_symbols = os.getenv("SYMBOLS", "btcusdt,ethusdt,solusdt")
    symbols = [s.strip() for s in raw_symbols.split(",") if s.strip()]
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")

    logger.info(f"Iniciando Producer para os símbolos: {symbols}")
    logger.info(f"Kafka bootstrap servers: {bootstrap_servers}")

    producer_config = {
        "bootstrap.servers": bootstrap_servers,
        "client.id": "binance-websocket-producer",
        "linger.ms": 100,
        "batch.num.messages": 1000,
    }
    producer = Producer(producer_config)

    url = build_combined_stream_url(base_url, symbols)
    logger.info(f"Conectando ao WebSocket: {url}")

    backoff = 1
    max_backoff = 60

    while True:
        try:
            async with connect(url, ping_interval=20, ping_timeout=60) as ws:
                logger.info("Conectado com sucesso ao WebSocket da Binance.")
                backoff = 1

                async for message in ws:
                    try:
                        envelope = json.loads(message)
                        stream_name = envelope.get("stream", "")
                        data = envelope.get("data", {})

                        if not stream_name or not data:
                            continue

                        if "@trade" in stream_name:
                            topic = "market.trades"
                        elif "@bookTicker" in stream_name:
                            topic = "market.book_ticker"
                        else:
                            continue

                        symbol = data.get("s", "UNKNOWN")
                        key = symbol.encode("utf-8")
                        value = json.dumps(data).encode("utf-8")

                        producer.produce(
                            topic=topic,
                            key=key,
                            value=value,
                            callback=delivery_report,
                        )
                        producer.poll(0)

                    except json.JSONDecodeError as e:
                        logger.error(f"Erro ao decodificar JSON da mensagem: {e}")
                    except (KeyError, TypeError, ValueError) as e:
                        logger.error(f"Erro ao processar estrutura da mensagem: {e}")

        except (TimeoutError, ConnectionClosed, WebSocketException, OSError) as e:
            logger.warning(f"Conexão perdida ou timeout ({e}). Reconectando em {backoff} segundos...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
        finally:
            producer.flush()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Producer interrompido pelo usuário.")
