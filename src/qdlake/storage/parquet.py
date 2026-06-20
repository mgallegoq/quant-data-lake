from pathlib import Path

import polars as pl


def write_parquet(df: pl.DataFrame, path: Path) -> None:
    """
    Write a Polars DataFrame to a Parquet file.

    The parent directory is created if it does not already exist.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)


def read_parquet(path: Path) -> pl.DataFrame:
    """
    Read a Parquet file into a Polars DataFrame.

    Raises FileNotFoundError if the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    return pl.read_parquet(path)