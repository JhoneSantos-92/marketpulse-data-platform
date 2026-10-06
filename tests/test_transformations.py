import polars as pl

from transformations.silver import fetch_bcb_exchange_rates


def test_fetch_bcb_exchange_rates_empty():
    df = fetch_bcb_exchange_rates("https://invalid-url-test.com")
    assert isinstance(df, pl.DataFrame)
    assert "exchange_date" in df.columns
    assert "usd_brl" in df.columns
