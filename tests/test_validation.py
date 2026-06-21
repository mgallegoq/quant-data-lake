from datetime import datetime, timezone

import polars as pl
import pytest

from qdlake.validation import (
    CANONICAL_PRICE_COLUMNS,
    standardize_daily_prices,
    validate_daily_prices,
)


def make_provider_prices() -> pl.DataFrame:
    """
    Build a small provider-shaped DataFrame.

    This mimics data returned by a provider such as Yahoo before
    standardization. Column names are intentionally provider-style:
    Date, Open, High, Low, Close, Volume.
    """
    return pl.DataFrame(
        {
            "Date": ["2024-01-03", "2024-01-02"],
            "Open": [101.0, 100.0],
            "High": [105.0, 104.0],
            "Low": [99.0, 98.0],
            "Close": [103.0, 102.0],
            "Volume": [1_100_000, 1_000_000],
            "symbol": ["AAPL", "AAPL"],
            "provider": ["yahoo", "yahoo"],
            "ingested_at": [
                datetime.now(timezone.utc),
                datetime.now(timezone.utc),
            ],
        }
    )


def make_valid_clean_prices() -> pl.DataFrame:
    """
    Build a small canonical clean DataFrame.
    """
    return standardize_daily_prices(make_provider_prices())


def test_standardize_daily_prices_returns_canonical_columns():
    df = make_provider_prices()

    clean = standardize_daily_prices(df)

    assert clean.columns == CANONICAL_PRICE_COLUMNS


def test_standardize_daily_prices_sorts_by_symbol_and_date():
    df = make_provider_prices()

    clean = standardize_daily_prices(df)

    dates = clean["date"].to_list()

    assert dates == sorted(dates)


def test_validate_daily_prices_accepts_valid_data():
    df = make_valid_clean_prices()

    validate_daily_prices(df)


def test_validate_daily_prices_rejects_empty_dataframe():
    df = pl.DataFrame()

    with pytest.raises(ValueError):
        validate_daily_prices(df)


def test_validate_daily_prices_rejects_duplicate_symbol_date():
    df = make_valid_clean_prices()

    duplicated = pl.concat([df, df.head(1)], how="vertical")

    with pytest.raises(ValueError):
        validate_daily_prices(duplicated)


def test_validate_daily_prices_rejects_non_positive_prices():
    df = make_valid_clean_prices().with_columns(
        pl.lit(0.0).alias("close")
    )

    with pytest.raises(ValueError):
        validate_daily_prices(df)


def test_validate_daily_prices_rejects_negative_volume():
    df = make_valid_clean_prices().with_columns(
        pl.lit(-1).alias("volume")
    )

    with pytest.raises(ValueError):
        validate_daily_prices(df)


def test_validate_daily_prices_rejects_high_below_low():
    df = make_valid_clean_prices().with_columns(
        pl.lit(90.0).alias("high"),
        pl.lit(100.0).alias("low"),
    )

    with pytest.raises(ValueError):
        validate_daily_prices(df)


def test_validate_daily_prices_rejects_open_outside_range():
    df = make_valid_clean_prices().with_columns(
        pl.lit(200.0).alias("open")
    )

    with pytest.raises(ValueError):
        validate_daily_prices(df)


def test_validate_daily_prices_rejects_close_outside_range():
    df = make_valid_clean_prices().with_columns(
        pl.lit(200.0).alias("close")
    )

    with pytest.raises(ValueError):
        validate_daily_prices(df)