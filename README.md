# Quant Data Lake

A small local data lake for quant research.

The goal of this project is to build a clean, modular, and testable market-data pipeline that can be used as the foundation for quantitative research, backtesting, and machine-learning experiments.

The project currently supports daily OHLCV equity data from Yahoo Finance through `yfinance`, stores raw and cleaned data separately, validates the cleaned data, writes it to Parquet, and queries it back using DuckDB.

This is primarily a learning project. The objective is not only to download prices, but to understand how professional quant research systems separate data ingestion, standardization, validation, storage, and querying.

---

## Project goals

The project is designed around a simple but important idea:

```text
external provider
    ↓
raw provider-shaped data
    ↓
standardization
    ↓
validated canonical data
    ↓
Parquet storage
    ↓
research queries
```

The main goals are:

* Keep raw data and clean data separate.
* Avoid provider-specific details leaking into the research layer.
* Define a canonical schema for daily price data.
* Validate data before storing it in the clean layer.
* Store data efficiently using Parquet.
* Query clean data with DuckDB.
* Provide a small command-line interface for ingestion and querying.

---

## Current status

Implemented:

* Project path management.
* Daily price schema.
* Abstract provider interface.
* Yahoo Finance provider.
* Stooq provider attempted, but the current `pandas-datareader` Stooq backend failed in this environment.
* Standardization of provider-shaped data into a canonical format.
* Validation of clean OHLCV data.
* Parquet read/write helpers.
* DuckDB-based query layer.
* CLI commands for ingestion and querying.

The current working provider is:

```text
YahooProvider
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
│   ├── clean/
│   │   └── prices/
│   └── features/
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
│       │   ├── stooq.py
│       │   └── yahoo.py
│       └── storage/
│           ├── __init__.py
│           └── parquet.py
└── tests/
```

---

## Data layers

The project separates data into different layers.

### Raw data

Raw data is the data returned by the external provider with minimal modification.

Example path:

```text
data/raw/prices/daily_prices_raw.parquet
```

Raw data may contain provider-specific columns such as:

```text
Date
Open
High
Low
Close
Adj Close
Volume
symbol
provider
ingested_at
```

The raw layer is useful for debugging and reproducibility. If the clean data looks wrong, the raw data can be inspected to understand what the provider returned.

### Clean data

Clean data is standardized and validated data.

Example path:

```text
data/clean/prices/daily_prices.parquet
```

The clean canonical schema is:

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

This is the format expected by the research layer.

### Feature data

The `data/features/` directory is reserved for future derived features such as:

```text
returns
log returns
rolling volatility
momentum
dollar volume
rolling beta
factor signals
```

Feature generation has not been implemented yet.

---

## Installation

Create and activate an environment:

```bash
conda create -n quant_lab python=3.10
conda activate quant_lab
```

Install the package in editable mode:

```bash
python -m pip install -e .
```

The project depends on:

```text
polars
duckdb
pyarrow
pydantic
typer
rich
yfinance
pandas
```

If needed, install them manually:

```bash
python -m pip install polars duckdb pyarrow pydantic typer rich yfinance pandas
```

---

## Command-line usage

After installing the package in editable mode, the `qdlake` command should be available.

Check the CLI:

```bash
qdlake --help
```

### Ingest prices

Download raw prices, standardize them, validate them, and save both raw and clean Parquet files:

```bash
qdlake ingest-prices \
  --symbols AAPL \
  --symbols MSFT \
  --start 2024-01-01 \
  --end 2024-01-10
```

This writes:

```text
data/raw/prices/daily_prices_raw.parquet
data/clean/prices/daily_prices.parquet
```

### Query prices

Query clean stored prices:

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

---

## Python usage

The same pipeline can be used directly from Python.

```python
from datetime import date

from qdlake.providers.yahoo import YahooProvider
from qdlake.validation import standardize_daily_prices, validate_daily_prices
from qdlake.storage.parquet import write_parquet
from qdlake.paths import CLEAN_PRICES_DIR

provider = YahooProvider()

raw = provider.get_daily_prices(
    symbols=["AAPL", "MSFT"],
    start=date(2024, 1, 1),
    end=date(2024, 1, 10),
)

clean = standardize_daily_prices(raw)

validate_daily_prices(clean)

write_parquet(
    clean,
    CLEAN_PRICES_DIR / "daily_prices.parquet",
)
```

Query clean data:

```python
from datetime import date

from qdlake.queries import query_daily_prices

prices = query_daily_prices(
    symbols=["AAPL"],
    start=date(2024, 1, 3),
    end=date(2024, 1, 8),
)

print(prices)
```

---

## Main modules

### `paths.py`

Defines project paths.

Important constants:

```python
PROJECT_ROOT
DATA_DIR
RAW_PRICES_DIR
CLEAN_PRICES_DIR
```

Also provides:

```python
ensure_data_directories()
```

This keeps path logic centralized and avoids fragile relative paths.

---

### `schemas.py`

Defines the row-level schema for one clean daily price bar.

The main model is:

```python
DailyPriceBar
```

It describes the expected fields for a single OHLCV observation.

The schema is a contract for what clean daily price data should look like.

---

### `providers/base.py`

Defines the abstract provider interface:

```python
PriceProvider
```

Every provider must implement:

```python
get_daily_prices(symbols, start, end)
```

and return a Polars DataFrame.

This lets the rest of the system use different providers through the same interface.

---

### `providers/yahoo.py`

Implements a concrete provider using `yfinance`.

The provider downloads data from Yahoo Finance and adds metadata columns:

```text
symbol
provider
ingested_at
```

The provider returns provider-shaped data. It does not validate or save data.

---

### `providers/stooq.py`

Contains an attempted Stooq provider using `pandas-datareader`.

In the current environment, all tested Stooq symbols failed with a `RemoteDataError`, including:

```text
AAPL
aapl
AAPL.US
aapl.us
^spx
^dji
```

This module is kept as an example of why provider-specific logic should be isolated. Provider failures should not affect the validation, storage, or query layers.

---

### `validation.py`

Contains two main public functions:

```python
standardize_daily_prices(df)
validate_daily_prices(df)
```

`standardize_daily_prices` converts provider-shaped data into the canonical schema.

`validate_daily_prices` checks that the standardized data is safe to store in the clean layer.

Validation checks include:

```text
non-empty dataframe
required columns present
no duplicate symbol/date rows
positive OHLC prices
non-negative volume
high >= low
open within [low, high]
close within [low, high]
```

---

### `storage/parquet.py`

Contains small wrappers around Polars Parquet I/O:

```python
write_parquet(df, path)
read_parquet(path)
```

The storage module is intentionally simple for now. Later it can be extended with partitioned datasets, append logic, compression settings, metadata, and atomic writes.

---

### `queries.py`

Contains the clean-data query layer.

The main function is:

```python
query_daily_prices(symbols, start=None, end=None, prices_path=None)
```

It queries the clean Parquet file using DuckDB and returns a Polars DataFrame.

This gives the project a lightweight local analytical database without needing a database server.

---

### `cli.py`

Exposes the project through the terminal.

Current commands:

```bash
qdlake ingest-prices
qdlake query-prices
```

The CLI is intentionally thin. It orchestrates the existing modules but does not contain the core logic itself.

---

## Current limitations

This is the first milestone, so several important features are not implemented yet.

Current limitations:

* Clean data is stored in a single Parquet file.
* New ingestions overwrite the previous clean file.
* No partitioning by symbol, provider, or year.
* No adjusted price handling yet.
* No corporate action handling.
* No split or dividend processing.
* No survivorship-bias-free universe construction.
* No delisted stock handling.
* No feature generation layer yet.
* No incremental ingestion.
* No logging system.
* No automated tests yet.
* No point-in-time data guarantees.
* No data versioning.

These limitations are intentional. The first milestone focuses on the basic architecture.

---

## Next milestones

### 1. Partitioned storage

Move from:

```text
data/clean/prices/daily_prices.parquet
```

to something like:

```text
data/clean/prices/provider=yahoo/symbol=AAPL/year=2024/part.parquet
```

This will make the data lake more scalable and realistic.

### 2. Incremental ingestion

Avoid redownloading the full history every time.

The system should detect which dates are already stored and only fetch missing data.

### 3. Adjusted prices and corporate actions

Add support for:

```text
adjusted_close
splits
dividends
total-return series
```

This is essential for realistic backtesting.

### 4. Feature generation

Build a feature layer with quantities such as:

```text
daily returns
log returns
rolling volatility
momentum
dollar volume
rolling mean
rolling beta
```

### 5. Tests

Add unit tests for:

```text
path creation
schema validation
provider interface
standardization
validation failures
Parquet read/write
query filtering
CLI behavior
```

### 6. Better provider abstraction

Add additional providers or provider options:

```text
CSVProvider
YahooProvider
StooqProvider
PolygonProvider
```

A future symbol-mapping layer should separate internal symbols from provider-specific symbols.

---

## Design principles

This project follows a few simple design principles.

### Keep provider logic isolated

External data providers are fragile. Their APIs, symbols, columns, and behavior can change.

Provider-specific logic should live inside:

```text
qdlake.providers
```

and should not leak into the rest of the project.

### Preserve raw data

Raw data should be saved before cleaning.

This makes the pipeline easier to debug and more reproducible.

### Validate before storing clean data

Clean data should be trusted data.

If validation fails, the clean file should not be written.

### Keep the CLI thin

The command-line interface should call the package modules.

It should not contain the core data logic itself.

### Prefer explicit schemas

The clean data schema should be boring, stable, and predictable.

The research layer should not care whether the original provider used `Close`, `close`, `Adj Close`, or some other convention.

---

## Example workflow

Full workflow:

```bash
python -m pip install -e .

qdlake ingest-prices \
  --symbols AAPL \
  --symbols MSFT \
  --start 2024-01-01 \
  --end 2024-01-10

qdlake query-prices \
  --symbols AAPL \
  --start 2024-01-03 \
  --end 2024-01-08
```

Expected result:

```text
1. Raw provider-shaped data is stored.
2. Clean canonical data is stored.
3. The queried result contains only the requested symbols and dates.
```

---

## Educational purpose

This project is intended as a learning tool for quant research engineering.

The important lesson is not simply how to download price data. The important lesson is how to structure a small research data system:

```text
providers
schemas
validation
storage
queries
CLI
```

This structure is the foundation for more advanced quant projects such as:

```text
factor research
backtesting
risk analysis
portfolio optimization
machine-learning alpha pipelines
```

The project should grow gradually, with each new feature added in a modular and testable way.
