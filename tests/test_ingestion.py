from ingestion.producer import build_combined_stream_url


def test_build_combined_stream_url():
    base_url = "wss://data-stream.binance.vision"
    symbols = ["btcusdt", "ethusdt"]
    url = build_combined_stream_url(base_url, symbols)
    assert url == "wss://data-stream.binance.vision/stream?streams=btcusdt@trade/btcusdt@bookTicker/ethusdt@trade/ethusdt@bookTicker"
