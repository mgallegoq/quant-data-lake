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
    Query standardized daily OHLCV price data from the clean Parquet layer.

    The function reads one or more Parquet files containing clean daily price
    data, filters the rows by symbol and optional date bounds, and returns the
    result as a Polars DataFrame. By default, it queries the partitioned clean
    price directory:

        data/clean/prices/provider=*/symbol=*/*.parquet

    This assumes that the data has already been ingested, standardized, and
    validated before being written to disk.

    Parameters
    ----------
    symbols:
        List of asset symbols to retrieve. Symbols are normalized to uppercase
        before querying.

    start:
        Optional inclusive lower bound for the trading date.

    end:
        Optional inclusive upper bound for the trading date.

    prices_path:
        Optional path or glob pattern pointing to the Parquet file(s) to query.
        If not provided, the default clean-price partitioned layout is used.

    Returns
    -------
    pl.DataFrame
        A Polars DataFrame containing the requested daily price data, sorted by
        symbol and date. The returned columns follow the canonical clean schema:

            symbol, date, open, high, low, close, volume, provider, ingested_at

    Raises
    ------
    ValueError
        If `symbols` is empty, or if both `start` and `end` are provided and
        `start > end`.

    Notes
    -----
    This function is part of the query layer. It should only retrieve already
    clean data from disk. It should not download, standardize, validate, or
    write market data.
    """

    if not symbols:
        raise ValueError("Symbol list cannot be empty.")

    if start is not None and end is not None and start > end:
        raise ValueError("Start date must be before end date.")

    symbols = [symbol.upper() for symbol in symbols]

    if prices_path is None:
        prices_path = CLEAN_PRICES_DIR / "provider=*" / "symbol=*" / "*.parquet"

    prices_path_str = str(prices_path)

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
        FROM read_parquet('{prices_path_str}', union_by_name=true)
        WHERE {where_sql}
        ORDER BY symbol, date
    """

    result = duckdb.sql(query).pl()

    return result