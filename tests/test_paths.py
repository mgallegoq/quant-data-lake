from datetime import date

from qdlake.paths import (
    price_file_name,
    raw_price_path,
    clean_price_path,
)


def test_price_file_name_contains_date_range():
    start = date(2024, 1, 1)
    end = date(2024, 1, 10)

    file_name = price_file_name(start, end)

    assert file_name == "daily_2024-01-01_2024-01-10.parquet"


def test_raw_price_path_uses_provider_symbol_and_date_range():
    path = raw_price_path(
        provider="yahoo",
        symbol="aapl",
        start=date(2024, 1, 1),
        end=date(2024, 1, 10),
    )

    assert "raw/prices" in str(path)
    assert "provider=yahoo" in str(path)
    assert "symbol=AAPL" in str(path)
    assert path.name == "daily_2024-01-01_2024-01-10.parquet"


def test_clean_price_path_uses_provider_symbol_and_date_range():
    path = clean_price_path(
        provider="Yahoo",
        symbol="msft",
        start=date(2024, 1, 1),
        end=date(2024, 1, 10),
    )

    assert "clean/prices" in str(path)
    assert "provider=yahoo" in str(path)
    assert "symbol=MSFT" in str(path)
    assert path.name == "daily_2024-01-01_2024-01-10.parquet"