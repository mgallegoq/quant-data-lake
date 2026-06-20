from datetime import date
from pathlib import Path

import duckdb
import polars as pl

from qdlake.paths import CLEAN_PRICES_DIR


def query_daily_prices(
    symbols: list[str],
    start: date | None = None,
    end: date | None = None,
    prices_path: Path | None = None,
) -> pl.DataFrame:
    """
    Query clean daily price data from a Parquet file.
    """

    if not symbols:
        raise ValueError("Symbol list cannot be empty.")

    if start is not None and end is not None and start > end:
        raise ValueError("Start date must be before end date.")

    symbols = [symbol.upper() for symbol in symbols]

    if prices_path is None:
        prices_path = CLEAN_PRICES_DIR / "daily_prices.parquet"

    if not prices_path.exists():
        raise FileNotFoundError(f"File not found: {prices_path}")

    symbol_sql = ", ".join(f"'{symbol}'" for symbol in symbols)

    where_clauses = [f"symbol IN ({symbol_sql})"]

    if start is not None:
        where_clauses.append(f"date >= DATE '{start}'")

    if end is not None:
        where_clauses.append(f"date <= DATE '{end}'")

    where_sql = " AND ".join(where_clauses)

    query = f"""
        SELECT
            symbol,
            date,
            open,
            high,
            low,
            close,
            volume,
            provider,
            ingested_at
        FROM read_parquet('{prices_path}')
        WHERE {where_sql}
        ORDER BY symbol, date
    """

    result = duckdb.sql(query).pl()

    return result