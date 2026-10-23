from datetime import UTC, datetime

import polars as pl

from transformations.gold import transform_gold_ohlcv


def test_gold_ohlcv_empty():
    # Testa comportamento graceful sem dados na silver
    transform_gold_ohlcv(
        "s3://invalid-bucket",
        {
            "AWS_ACCESS_KEY_ID": "a",
            "AWS_SECRET_ACCESS_KEY": "b",
            "AWS_ENDPOINT_URL": "http://localhost:8333",
            "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
        },
    )


def test_ohlcv_aggregation_logic():
    # Testa agregação OHLCV com Polars
    df = pl.DataFrame({
        "symbol": ["btcusdt", "btcusdt", "btcusdt"],
        "trade_dt": [
            datetime(2026, 1, 1, 12, 0, 15, tzinfo=UTC),
            datetime(2026, 1, 1, 12, 0, 30, tzinfo=UTC),
            datetime(2026, 1, 1, 12, 1, 5, tzinfo=UTC),
        ],
        "price": [100.0, 105.0, 102.0],
        "quantity": [1.0, 2.0, 1.5],
        "price_brl": [550.0, 577.5, 561.0],
        "trade_id": [1, 2, 3],
    })

    df_ohlcv = (
        df.group_by_dynamic(
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
            pl.count("trade_id").alias("trade_count"),
        ])
    )

    assert len(df_ohlcv) == 2
    assert df_ohlcv["open"].to_list() == [100.0, 102.0]
    assert df_ohlcv["high"].to_list() == [105.0, 102.0]
    assert df_ohlcv["trade_count"].to_list() == [2, 1]
