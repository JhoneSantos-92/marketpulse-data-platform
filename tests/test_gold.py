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
