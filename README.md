# Quant Data Lake

A local market-data lake for quantitative research.

This project provides a small, modular pipeline for downloading, standardizing, validating, storing, and querying daily OHLCV market data. It is designed as a learning-oriented quant engineering project, with a focus on clean architecture rather than feature generation or strategy logic.

The current implementation supports daily equity price data from Yahoo Finance through `yfinance`, stores raw and clean data separately, saves each symbol independently using a partitioned folder layout, and queries clean data with DuckDB.

---

## Project purpose

The goal of this project is to build a reliable local data layer for downstream quantitative research.

The data lake is responsible for answering questions such as:

```text
Give me clean AAPL daily prices from 2024-01-01 to 2024-01-10.
```

It is not responsible for computing trading signals, features, factors, portfolio weights, or backtests. Those should live in downstream research projects.

The core workflow is:

```text
external provider
    ↓
raw provider-shaped data
    ↓
standardization
    ↓
validation
    ↓
clean Parquet storage
    ↓
DuckDB queries
    ↓
research projects / notebooks / backtests
```

---

## Current features

Implemented:

* Project path management.
* Daily OHLCV schema definition.
* Abstract price provider interface.
* Yahoo Finance provider.
* Raw and clean data separation.
* Standardization of provider-shaped data.
* Validation of clean OHLCV data.
* Per-symbol Parquet storage.
* Partitioned clean-data layout.
* DuckDB-based query layer.
* Command-line interface.
* Unit tests for validation, storage, paths, queries, and CLI loading.

The project currently uses:

```text
yfinance
polars
duckdb
pyarrow
pydantic
typer
rich
pytest
```

---

## Project structure

```text
quant-data-lake/
├── README.md
├── pyproject.toml
├── data/
│   ├── raw/
│   │   └── prices/
│   └── clean/
│       └── prices/
├── src/
│   └── qdlake/
│       ├── __init__.py
│       ├── paths.py
│       ├── schemas.py
│       ├── validation.py
│       ├── queries.py
│       ├── cli.py
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── yahoo.py
│       │   └── stooq.py
│       └── storage/
│           ├── __init__.py
│           └── parquet.py
└── tests/
    ├── test_validation.py
    ├── test_storage.py
    ├── test_queries.py
    ├── test_paths.py
    └── test_cli.py
```

---

## Data layout

The project stores raw and clean data separately.

### Raw data

Raw data is provider-shaped data saved with minimal transformation.

Example:

```text
data/raw/prices/provider=yahoo/symbol=AAPL/daily_2024-01-01_2024-01-10.parquet
```

Raw data is useful for debugging and reproducibility. If the clean data looks wrong, the raw file can be inspected to see what the provider originally returned.

### Clean data

Clean data is standardized, validated, and stored using the canonical schema.

Example:

```text
data/clean/prices/provider=yahoo/symbol=AAPL/daily_2024-01-01_2024-01-10.parquet
```

Each symbol is stored independently. This prevents one ingestion from overwriting data for another symbol.

The clean data layout is:

```text
data/clean/prices/
└── provider=yahoo/
    ├── symbol=AAPL/
    │   └── daily_2024-01-01_2024-01-10.parquet
    └── symbol=MSFT/
        └── daily_2024-01-01_2024-01-10.parquet
```

This follows a simple partition-style convention:

```text
provider=<provider_name>/symbol=<symbol>/daily_<start>_<end>.parquet
```

---

## Canonical clean schema

The clean price schema is:

```text
symbol
date
open
high
low
close
volume
provider
ingested_at
```

where:

* `symbol` is the uppercase asset symbol.
* `date` is the trading date.
* `open`, `high`, `low`, and `close` are strictly positive prices.
* `volume` is non-negative.
* `provider` identifies the data source.
* `ingested_at` records when the data was downloaded.

---

## Installation

Create and activate a Python environment:

```bash
conda create -n quant_lab python=3.10
conda activate quant_lab
```

Install the project in editable mode:

```bash
python -m pip install -e .
```

If needed, install the required dependencies manually:

```bash
python -m pip install polars duckdb pyarrow pydantic typer rich yfinance pandas pytest
```

Check that the CLI is available:

```bash
qdlake --help
```

---

## Command-line usage

### Ingest prices

Download, standardize, validate, and save daily prices:

```bash
qdlake ingest-prices \
  --symbols AAPL \
  --symbols MSFT \
  --start 2024-01-01 \
  --end 2024-01-10
```

This creates one raw file and one clean file per symbol.

Example output files:

```text
data/raw/prices/provider=yahoo/symbol=AAPL/daily_2024-01-01_2024-01-10.parquet
data/raw/prices/provider=yahoo/symbol=MSFT/daily_2024-01-01_2024-01-10.parquet

data/clean/prices/provider=yahoo/symbol=AAPL/daily_2024-01-01_2024-01-10.parquet
data/clean/prices/provider=yahoo/symbol=MSFT/daily_2024-01-01_2024-01-10.parquet
```

Inspect the created files:

```bash
find data -type f | sort
```

### Query prices

Query clean prices from the partitioned clean layer:

```bash
qdlake query-prices \
  --symbols AAPL \
  --start 2024-01-03 \
  --end 2024-01-08
```

Query multiple symbols:

```bash
qdlake query-prices \
  --symbols AAPL \
  --symbols MSFT \
  --start 2024-01-03 \
  --end 2024-01-08
```

The query layer reads matching clean Parquet files using DuckDB.

---

## Python usage

The same pipeline can be used directly from Python.

```python
from datetime import date

from qdlake.providers.yahoo import YahooProvider
from qdlake.validation import standardize_daily_prices, validate_daily_prices
from qdlake.storage.parquet import write_parquet
from qdlake.paths import clean_price_path, raw_price_path

provider = YahooProvider()

symbols = ["AAPL", "MSFT"]
start = date(2024, 1, 1)
end = date(2024, 1, 10)

raw = provider.get_daily_prices(
    symbols=symbols,
    start=start,
    end=end,
)

clean = standardize_daily_prices(raw)
validate_daily_prices(clean)

for symbol in symbols:
    symbol = symbol.upper()

    raw_symbol = raw.filter(raw["symbol"] == symbol)
    clean_symbol = clean.filter(clean["symbol"] == symbol)

    write_parquet(
        raw_symbol,
        raw_price_path(provider.name, symbol, start, end),
    )

    write_parquet(
        clean_symbol,
        clean_price_path(provider.name, symbol, start, end),
    )
```

Query clean data:

```python
from datetime import date

from qdlake.queries import query_daily_prices

prices = query_daily_prices(
    symbols=["AAPL", "MSFT"],
    start=date(2024, 1, 3),
    end=date(2024, 1, 8),
)

print(prices)
```

---

## Main modules

### `paths.py`

Defines project paths and file-naming conventions.

Important constants:

```python
PROJECT_ROOT
DATA_DIR
RAW_PRICES_DIR
CLEAN_PRICES_DIR
```

Important functions:

```python
ensure_data_directories()
price_file_name()
raw_price_path()
clean_price_path()
```

This module centralizes the storage layout so file paths are not hard-coded across the project.

---

### `schemas.py`

Defines the row-level schema for clean daily price data.

The main model is:

```python
DailyPriceBar
```

This schema defines what one canonical OHLCV observation should look like.

---

### `providers/base.py`

Defines the abstract provider interface:

```python
PriceProvider
```

Every price provider must implement:

```python
get_daily_prices(symbols, start, end)
```

and return a Polars DataFrame.

The provider layer is responsible for downloading data, but not for validation or storage.

---

### `providers/yahoo.py`

Implements a Yahoo Finance provider using `yfinance`.

The provider returns provider-shaped daily price data and adds metadata columns:

```text
symbol
provider
ingested_at
```

Standardization and validation happen later in `validation.py`.

---

### `providers/stooq.py`

Contains an attempted Stooq provider using `pandas-datareader`.

The Stooq backend failed in the current environment, so Yahoo Finance is currently used as the working provider. Keeping provider logic isolated makes this kind of failure easy to handle without affecting the rest of the project.

---

### `validation.py`

Contains the data standardization and validation logic.

Main functions:

```python
standardize_daily_prices(df)
validate_daily_prices(df)
```

`standardize_daily_prices` converts provider-shaped data into the canonical clean schema.

`validate_daily_prices` checks that the clean data satisfies the project’s assumptions.

Validation checks include:

```text
non-empty DataFrame
required columns present
no duplicate symbol/date rows
strictly positive OHLC prices
non-negative volume
high >= low
open within [low, high]
close within [low, high]
```

---

### `storage/parquet.py`

Contains simple Parquet I/O helpers:

```python
write_parquet(df, path)
read_parquet(path)
```

The storage layer is intentionally small. It writes and reads Parquet files, but does not validate data.

---

### `queries.py`

Contains the clean-data query layer.

Main function:

```python
query_daily_prices(symbols, start=None, end=None, prices_path=None)
```

By default, this function queries all clean price files matching:

```text
data/clean/prices/provider=*/symbol=*/*.parquet
```

It filters by symbol and optional date bounds, then returns a Polars DataFrame sorted by symbol and date.

This module should only retrieve already clean data from disk. It should not download, standardize, validate, or write data.

---

### `cli.py`

Exposes the project through the terminal.

Current commands:

```bash
qdlake ingest-prices
qdlake query-prices
```

The CLI is intentionally thin. It orchestrates the provider, validation, storage, and query layers without duplicating their logic.

---

## Tests

The project uses `pytest`.

Run all tests with:

```bash
python -m pytest
```

Current test modules:

```text
tests/test_validation.py
tests/test_storage.py
tests/test_queries.py
tests/test_paths.py
tests/test_cli.py
```

The tests cover:

* Standardization into the canonical schema.
* Validation of valid and invalid OHLCV data.
* Parquet write/read behavior.
* Missing-file behavior.
* Partitioned query behavior.
* Path naming conventions.
* CLI command registration.

Provider downloads are not tested against the real internet. This is intentional: unit tests should be deterministic and should not depend on network availability, external API behavior, or rate limits.

---

## Design principles

### Keep raw and clean data separate

Raw data is what the provider returned.

Clean data is what the project trusts.

Keeping both layers makes the pipeline easier to debug and reason about.

### Save symbols independently

Each symbol is saved in its own file. This prevents one ingestion from overwriting data for another asset.

### Keep provider logic isolated

External providers can change or fail. Provider-specific code lives in `qdlake.providers`, while the rest of the project works with standardized data.

### Validate before writing clean data

Only validated data should enter the clean layer.

If validation fails, the clean file should not be written.

### Keep the query layer read-only

The query layer reads clean data. It should not download, standardize, validate, or mutate data.

### Keep feature engineering outside this project

This project is a data lake, not a factor library or backtester.

Derived quantities such as returns, volatility, momentum, signals, portfolio weights, and performance metrics should be computed in downstream projects.

---

## Current limitations

The project is intentionally small and focused. Current limitations include:

* No incremental ingestion.
* No automatic merging of overlapping date ranges.
* Re-ingesting the same provider-symbol-date range overwrites that exact file.
* No adjusted-price handling.
* No split or dividend processing.
* No survivorship-bias-free universe management.
* No delisted asset handling.
* No provider reconciliation.
* No point-in-time database guarantees.
* No data versioning.
* No intraday data.
* No live trading functionality.

These limitations are acceptable for the current milestone.

---

## Possible future improvements

Useful next improvements include:

```text
provider selection in the CLI
incremental ingestion
overlap detection between stored files
append/merge logic for existing symbols
better logging
data catalog / ingestion metadata
adjusted close support
corporate action support
CSV provider for local files
```

The next major conceptual step should probably be a separate downstream project, such as a factor research library or tear-sheet generator, that consumes this data lake instead of expanding this package into a full research framework.

---

## Example workflow

A typical workflow is:

```bash
python -m pip install -e .

qdlake ingest-prices \
  --symbols AAPL \
  --symbols MSFT \
  --start 2024-01-01 \
  --end 2024-01-10

qdlake query-prices \
  --symbols AAPL \
  --symbols MSFT \
  --start 2024-01-03 \
  --end 2024-01-08

python -m pytest
```

This downloads data, stores raw and clean Parquet files per symbol, queries the clean layer, and verifies that the main project contracts still hold.

---

## Educational purpose

This project is intended as a practical introduction to quant data engineering.

The main lesson is not how to download prices. The main lesson is how to structure a small but reliable data system around clear responsibilities:

```text
providers
schemas
validation
storage
queries
CLI
tests
```

This structure can support downstream projects such as:

```text
factor research
strategy analysis
portfolio construction
performance tear sheets
backtesting
machine-learning alpha research
```
