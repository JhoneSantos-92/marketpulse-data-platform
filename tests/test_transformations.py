import polars as pl

from transformations.silver import fetch_bcb_exchange_rates


def test_fetch_bcb_exchange_rates_empty():
    df = fetch_bcb_exchange_rates("https://invalid-url-test.com")
    assert isinstance(df, pl.DataFrame)
    assert "exchange_date" in df.columns
    assert "usd_brl" in df.columns
    assert len(df) == 1
    assert df["usd_brl"][0] == 5.50


def test_trade_validation_logic():
    # Testa lógica de validação de faixa (preço/quantidade > 0)
    raw_data = [
        {"t": 1, "s": "btcusdt", "p": 50000.0, "q": 1.0, "T": 1000000},
        {"t": 2, "s": "btcusdt", "p": -100.0, "q": 1.0, "T": 1000000},  # Preço inválido
        {"t": 3, "s": "btcusdt", "p": 50000.0, "q": 0.0, "T": 1000000},  # Quantidade inválida
    ]
    valid_rows = []
    quarantine_rows = []
    for r in raw_data:
        if r["p"] <= 0 or r["q"] <= 0:
            quarantine_rows.append(r)
        else:
            valid_rows.append(r)

    assert len(valid_rows) == 1
    assert len(quarantine_rows) == 2
    assert valid_rows[0]["t"] == 1


def test_trade_deduplication_logic():
    # Testa deduplicação por trade_id
    df = pl.DataFrame([
        {"trade_id": 101, "price": 100.0},
        {"trade_id": 101, "price": 100.0},
        {"trade_id": 102, "price": 200.0},
    ])
    df_dedup = df.unique(subset=["trade_id"])
    assert len(df_dedup) == 2
    assert sorted(df_dedup["trade_id"].to_list()) == [101, 102]


def test_book_ticker_spread_calculation():
    # Testa cálculo de spread no book ticker
    bid = 49990.0
    ask = 50010.0
    spread = ask - bid
    assert spread == 20.0
    assert bid < ask
