from pathlib import Path

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