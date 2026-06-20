from datetime import date
from typing import Annotated

import typer
from rich import print

from qdlake.paths import ensure_data_directories, RAW_PRICES_DIR, CLEAN_PRICES_DIR
from qdlake.providers.yahoo import YahooProvider
from qdlake.storage.parquet import write_parquet
from qdlake.validation import standardize_daily_prices, validate_daily_prices
from qdlake.queries import query_daily_prices


app = typer.Typer()


@app.command()
def ingest_prices(
    symbols: Annotated[list[str], typer.Option("--symbols", "-s")],
    start: Annotated[str, typer.Option("--start")],
    end: Annotated[str, typer.Option("--end")],
) -> None:
    """
    Download daily prices, save raw data, clean it, validate it,
    and write clean data to Parquet.
    """

    ensure_data_directories()

    provider = YahooProvider()

    print(f"[bold]Downloading prices from {provider.name}...[/bold]")
    start_date = parse_date(start)
    end_date = parse_date(end)
    raw_df = provider.get_daily_prices(
        symbols=symbols,
        start=start_date,
        end=end_date,
    )

    if raw_df.is_empty():
        print("[red]No data returned.[/red]")
        raise typer.Exit(code=1)

    raw_path = RAW_PRICES_DIR / "daily_prices_raw.parquet"
    write_parquet(raw_df, raw_path)

    print(f"[green]Saved raw data to:[/green] {raw_path}")

    clean_df = standardize_daily_prices(raw_df)

    print("[bold]Validating clean data...[/bold]")
    validate_daily_prices(clean_df)

    clean_path = CLEAN_PRICES_DIR / "daily_prices.parquet"
    write_parquet(clean_df, clean_path)

    print(f"[green]Saved clean data to:[/green] {clean_path}")
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
    start_date = parse_date(start)
    end_date = parse_date(end)
    df = query_daily_prices(
        symbols=symbols,
        start=start_date,
        end=end_date,
    )

    print(df)

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