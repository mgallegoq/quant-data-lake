import polars as pl
import pytest

from qdlake.storage.parquet import read_parquet, write_parquet


def test_write_and_read_parquet_roundtrip(tmp_path):
    df = pl.DataFrame(
        {
            "symbol": ["AAPL", "MSFT"],
            "close": [100.0, 200.0],
        }
    )

    path = tmp_path / "prices" / "test_prices.parquet"

    write_parquet(df, path)

    loaded = read_parquet(path)

    assert loaded.equals(df)


def test_write_parquet_creates_parent_directories(tmp_path):
    df = pl.DataFrame(
        {
            "symbol": ["AAPL"],
            "close": [100.0],
        }
    )

    path = tmp_path / "nested" / "prices" / "test.parquet"

    write_parquet(df, path)

    assert path.exists()


def test_read_parquet_raises_for_missing_file(tmp_path):
    path = tmp_path / "missing.parquet"

    with pytest.raises(FileNotFoundError):
        read_parquet(path)