import json
import logging
import os
import sys
import time
from datetime import UTC, datetime

import polars as pl
from confluent_kafka import Consumer, KafkaError
from deltalake import write_deltalake
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("streaming_consumer")

def get_s3_storage_options() -> dict[str, str]:
    return {
        "AWS_ACCESS_KEY_ID": os.getenv("S3_ACCESS_KEY", "admin"),
        "AWS_SECRET_ACCESS_KEY": os.getenv("S3_SECRET_KEY", "admin"),
        "AWS_ENDPOINT_URL": os.getenv("S3_ENDPOINT", "http://localhost:8333"),
        "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
    }

def process_batch(messages: list, topic: str, storage_uri: str, storage_options: dict) -> None:
    if not messages:
        return

    data_rows = []
    for msg in messages:
        try:
            payload = json.loads(msg.value().decode("utf-8"))
            symbol = payload.get("s", "UNKNOWN").lower()
            
            event_ts = payload.get("E") or payload.get("T") or int(time.time() * 1000)
            dt = datetime.fromtimestamp(event_ts / 1000, tz=UTC)
            
            date_str = dt.strftime("%Y-%m-%d")
            hour_str = dt.strftime("%H")

            row = {
                "raw_json": msg.value().decode("utf-8"),
                "symbol": symbol,
                "date": date_str,
                "hour": hour_str,
                "partition_date": date_str,
                "partition_hour": hour_str,
                "kafka_partition": msg.partition(),
                "kafka_offset": msg.offset(),
                "ingestion_timestamp": int(time.time() * 1000),
            }
            data_rows.append(row)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Erro ao processar mensagem individual: {e}")

    if not data_rows:
        return

    df = pl.DataFrame(data_rows)

    if "trades" in topic:
        table_path = f"{storage_uri}/bronze/trades"
    elif "book_ticker" in topic:
        table_path = f"{storage_uri}/bronze/book_ticker"
    else:
        table_path = f"{storage_uri}/bronze/unknown"

    logger.info(f"Escrevendo lote de {len(data_rows)} registros para o Delta Lake em {table_path}")

    try:
        write_deltalake(
            table_path,
            df.to_arrow(),
            mode="append",
            storage_options=storage_options,
            partition_by=["symbol", "partition_date", "partition_hour"],
        )
    except Exception as e:
        logger.error(f"Erro ao gravar no Delta Lake ({table_path}): {e}")
        raise

def main() -> None:
    load_dotenv()

    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
    storage_uri = os.getenv("STORAGE_URI", "s3://marketpulse-lake")
    group_id = "marketpulse-bronze-consumer-group"
    topics = ["market.trades", "market.book_ticker"]

    logger.info(f"Iniciando Consumer para os tópicos: {topics}")
    logger.info(f"Kafka bootstrap servers: {bootstrap_servers}")
    logger.info(f"Storage URI: {storage_uri}")

    conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }

    consumer = Consumer(conf)
    consumer.subscribe(topics)

    storage_options = get_s3_storage_options()

    batch_size = 500
    batch_timeout_sec = 5.0
    accumulated_messages = {topic: [] for topic in topics}
    last_flush_time = time.time()

    try:
        while True:
            timeout = 1.0
            msg = consumer.poll(timeout)
            current_time = time.time()

            if msg is None:
                if current_time - last_flush_time >= batch_timeout_sec:
                    for t, msgs in accumulated_messages.items():
                        if msgs:
                            process_batch(msgs, t, storage_uri, storage_options)
                            consumer.commit(asynchronous=False)
                            accumulated_messages[t] = []
                    last_flush_time = current_time
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Erro no Kafka: {msg.error()}")
                    break

            topic = msg.topic()
            accumulated_messages[topic].append(msg)

            if len(accumulated_messages[topic]) >= batch_size:
                process_batch(accumulated_messages[topic], topic, storage_uri, storage_options)
                consumer.commit(asynchronous=False)
                accumulated_messages[topic] = []
                last_flush_time = current_time

    except KeyboardInterrupt:
        logger.info("Consumer interrompido pelo usuário.")
    finally:
        consumer.close()

if __name__ == "__main__":
    main()
