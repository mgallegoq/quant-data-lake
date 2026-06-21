import polars as pl
from datetime import date
from typing import Annotated

import typer
from rich import print

from qdlake.paths import (
    ensure_data_directories,
    raw_price_path,
    clean_price_path,
)
from qdlake.providers.yahoo import YahooProvider
from qdlake.storage.parquet import write_parquet
from qdlake.validation import standardize_daily_prices, validate_daily_prices
from qdlake.queries import query_daily_prices


app = typer.Typer()


def parse_date(value: str) -> date:
    """
    Parse a YYYY-MM-DD string into a date object.
    """
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise typer.BadParameter(
            f"Invalid date {value!r}. Expected format: YYYY-MM-DD."
        ) from exc


@app.command()
def ingest_prices(
    symbols: Annotated[list[str], typer.Option("--symbols", "-s")],
    start: Annotated[str, typer.Option("--start")],
    end: Annotated[str, typer.Option("--end")],
) -> None:
    """
    Download daily prices, save raw data by symbol, clean it, validate it,
    and write clean data by symbol to Parquet.
    """

    start_date = parse_date(start)
    end_date = parse_date(end)

    ensure_data_directories()

    provider = YahooProvider()

    print(f"[bold]Downloading prices from {provider.name}...[/bold]")

    raw_df = provider.get_daily_prices(
        symbols=symbols,
        start=start_date,
        end=end_date,
    )

    if raw_df.is_empty():
        print("[red]No data returned.[/red]")
        raise typer.Exit(code=1)

    clean_df = standardize_daily_prices(raw_df)

    print("[bold]Validating clean data...[/bold]")
    validate_daily_prices(clean_df)

    for symbol in symbols:
        canonical_symbol = symbol.upper()

        symbol_raw_df = raw_df.filter(pl.col("symbol") == canonical_symbol)
        symbol_clean_df = clean_df.filter(pl.col("symbol") == canonical_symbol)

        if symbol_raw_df.is_empty() or symbol_clean_df.is_empty():
            print(f"[yellow]No data to save for {canonical_symbol}.[/yellow]")
            continue

        raw_path = raw_price_path(
            provider=provider.name,
            symbol=canonical_symbol,
            start=start_date,
            end=end_date,
        )

        clean_path = clean_price_path(
            provider=provider.name,
            symbol=canonical_symbol,
            start=start_date,
            end=end_date,
        )

        write_parquet(symbol_raw_df, raw_path)
        write_parquet(symbol_clean_df, clean_path)

        print(f"[green]Saved raw data:[/green] {raw_path}")
        print(f"[green]Saved clean data:[/green] {clean_path}")

    print("[bold]Rows by symbol:[/bold]")
    print(clean_df.group_by("symbol").len().sort("symbol"))

    print("[bold]Preview:[/bold]")
    print(clean_df.head(10))


@app.command()
def query_prices(
    symbols: Annotated[list[str], typer.Option("--symbols", "-s")],
    start: Annotated[str | None, typer.Option("--start")] = None,
    end: Annotated[str | None, typer.Option("--end")] = None,
) -> None:
    """
    Query clean prices.
    """

    start_date = parse_date(start) if start is not None else None
    end_date = parse_date(end) if end is not None else None

    df = query_daily_prices(
        symbols=symbols,
        start=start_date,
        end=end_date,
    )

    print(df)