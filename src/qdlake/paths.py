from pathlib import Path
from datetime import date

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_PRICES_DIR = DATA_DIR / "raw" / "prices"
CLEAN_PRICES_DIR = DATA_DIR / "clean" / "prices"

def ensure_data_directories() -> None:
    """
    Ensure that the data directories exist.
    """

    RAW_PRICES_DIR.mkdir(parents=True, exist_ok=True)
    CLEAN_PRICES_DIR.mkdir(parents=True, exist_ok=True)


def price_file_name(start: date, end: date) -> str:
    """
    Build a filename for a daily price file covering a date range.

    Example:
        daily_2024-01-01_2024-01-10.parquet
    """
    return f"daily_{start}_{end}.parquet"


def raw_price_path(
    provider: str,
    symbol: str,
    start: date,
    end: date,
) -> Path:
    """
    Return the raw price path for one provider, one symbol, and one date range.
    """
    return (
        RAW_PRICES_DIR
        / f"provider={provider.lower()}"
        / f"symbol={symbol.upper()}"
        / price_file_name(start, end)
    )


def clean_price_path(
    provider: str,
    symbol: str,
    start: date,
    end: date,
) -> Path:
    """
    Return the clean price path for one provider, one symbol, and one date range.
    """
    return (
        CLEAN_PRICES_DIR
        / f"provider={provider.lower()}"
        / f"symbol={symbol.upper()}"
        / price_file_name(start, end)
    )