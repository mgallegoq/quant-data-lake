from datetime import date, datetime, timezone

import polars as pl
import pytest

from qdlake.queries import query_daily_prices
from qdlake.storage.parquet import write_parquet


def make_clean_prices() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "symbol": ["AAPL", "AAPL", "MSFT", "MSFT"],
            "date": [
                date(2024, 1, 2),
                date(2024, 1, 3),
                date(2024, 1, 2),
                date(2024, 1, 3),
            ],
            "open": [100.0, 101.0, 200.0, 201.0],
            "high": [105.0, 106.0, 205.0, 206.0],
            "low": [99.0, 100.0, 199.0, 200.0],
            "close": [103.0, 104.0, 203.0, 204.0],
            "volume": [1_000_000, 1_100_000, 2_000_000, 2_100_000],
            "provider": ["test", "test", "test", "test"],
            "ingested_at": [datetime.now(timezone.utc)] * 4,
        }
    )


def write_partitioned_test_data(base_path):
    df = make_clean_prices()

    for symbol in ["AAPL", "MSFT"]:
        symbol_df = df.filter(pl.col("symbol") == symbol)
        path = (
            base_path
            / "provider=test"
            / f"symbol={symbol}"
            / "daily_2024-01-01_2024-01-10.parquet"
        )
        write_parquet(symbol_df, path)

    return base_path / "provider=*" / "symbol=*" / "*.parquet"


def test_query_daily_prices_filters_symbols(tmp_path):
    prices_glob = write_partitioned_test_data(tmp_path)

    result = query_daily_prices(
        symbols=["AAPL"],
        prices_path=prices_glob,
    )

    assert result["symbol"].unique().to_list() == ["AAPL"]


def test_query_daily_prices_filters_date_range(tmp_path):
    prices_glob = write_partitioned_test_data(tmp_path)

    result = query_daily_prices(
        symbols=["AAPL", "MSFT"],
        start=date(2024, 1, 3),
        end=date(2024, 1, 3),
        prices_path=prices_glob,
    )

    assert result["date"].min() == date(2024, 1, 3)
    assert result["date"].max() == date(2024, 1, 3)


def test_query_daily_prices_rejects_empty_symbols(tmp_path):
    prices_glob = write_partitioned_test_data(tmp_path)

    with pytest.raises(ValueError):
        query_daily_prices(
            symbols=[],
            prices_path=prices_glob,
        )


def test_query_daily_prices_rejects_invalid_date_range(tmp_path):
    prices_glob = write_partitioned_test_data(tmp_path)

    with pytest.raises(ValueError):
        query_daily_prices(
            symbols=["AAPL"],
            start=date(2024, 1, 10),
            end=date(2024, 1, 1),
            prices_path=prices_glob,
        )