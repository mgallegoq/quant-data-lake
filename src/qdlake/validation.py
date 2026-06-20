import polars as pl


CANONICAL_PRICE_COLUMNS = [
    "symbol",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "provider",
    "ingested_at",
]


RENAME_MAP = {
    "Date": "date",
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Volume": "volume",
}


def _rename_daily_price_columns(df: pl.DataFrame) -> pl.DataFrame:
    """
    Rename provider-specific columns to canonical column names.
    """

    existing_renames = {
        old: new
        for old, new in RENAME_MAP.items()
        if old in df.columns
    }

    return df.rename(existing_renames)


def _check_required_price_columns(df: pl.DataFrame) -> None:
    """
    Check that all canonical price columns are present.
    """

    missing = set(CANONICAL_PRICE_COLUMNS) - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns after standardization: {sorted(missing)}"
        )


def _cast_daily_price_columns(df: pl.DataFrame) -> pl.DataFrame:
    """
    Cast daily price columns to the expected canonical dtypes.
    """

    return df.with_columns(
        [
            pl.col("symbol").cast(pl.Utf8),
            pl.col("date").cast(pl.Date),
            pl.col("open").cast(pl.Float64),
            pl.col("high").cast(pl.Float64),
            pl.col("low").cast(pl.Float64),
            pl.col("close").cast(pl.Float64),
            pl.col("volume").cast(pl.Int64),
            pl.col("provider").cast(pl.Utf8),
            pl.col("ingested_at").cast(pl.Datetime),
        ]
    )


def standardize_daily_prices(df: pl.DataFrame) -> pl.DataFrame:
    """
    Convert provider-shaped daily price data into the canonical schema.
    """

    if df.is_empty():
        return df

    df = _rename_daily_price_columns(df)

    _check_required_price_columns(df)

    df = _cast_daily_price_columns(df)

    df = df.select(CANONICAL_PRICE_COLUMNS)

    df = df.sort(["symbol", "date"])

    return df

def validate_daily_prices(df: pl.DataFrame) -> None:
    """
    Validate standardized daily OHLCV price data.

    This function assumes that the DataFrame has already been passed through
    standardize_daily_prices, so it should already use the canonical schema:

        symbol, date, open, high, low, close, volume, provider, ingested_at

    The function raises ValueError if the data is invalid.
    If no error is raised, the data is considered valid.
    """

    # 1. Check that the DataFrame is not empty.
    if df.is_empty():
        raise ValueError("DataFrame is empty.")

    # 2. Check that all required canonical columns are present.
    missing = set(CANONICAL_PRICE_COLUMNS) - set(df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # 3. Check that each (symbol, date) pair appears only once.
    duplicates = (
        df.group_by(["symbol", "date"])
        .len()
        .filter(pl.col("len") > 1)
    )

    if duplicates.height > 0:
        raise ValueError("Duplicate rows found for the same symbol and date.")

    # 4. Check that OHLC prices are strictly positive.
    bad_prices = df.filter(
        (pl.col("open") <= 0)
        | (pl.col("high") <= 0)
        | (pl.col("low") <= 0)
        | (pl.col("close") <= 0)
    )

    if bad_prices.height > 0:
        raise ValueError("OHLC prices must be strictly positive.")

    # 5. Check that volume is non-negative.
    bad_volume = df.filter(pl.col("volume") < 0)

    if bad_volume.height > 0:
        raise ValueError("Volume must be non-negative.")

    # 6. Check that high >= low.
    bad_high_low = df.filter(pl.col("high") < pl.col("low"))

    if bad_high_low.height > 0:
        raise ValueError("High price must be greater than or equal to low price.")

    # 7. Check that open lies inside [low, high].
    bad_open = df.filter(
        (pl.col("open") < pl.col("low"))
        | (pl.col("open") > pl.col("high"))
    )

    if bad_open.height > 0:
        raise ValueError(
            "Open price must be within the daily range "
            "(low <= open <= high)."
        )

    # 8. Check that close lies inside [low, high].
    bad_close = df.filter(
        (pl.col("close") < pl.col("low"))
        | (pl.col("close") > pl.col("high"))
    )

    if bad_close.height > 0:
        raise ValueError(
            "Close price must be within the daily range "
            "(low <= close <= high)."
        )