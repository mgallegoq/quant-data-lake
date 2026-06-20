from datetime import date, datetime, timezone

import pandas as pd
import polars as pl
import yfinance as yf

from qdlake.providers.base import PriceProvider


class YahooProvider(PriceProvider):
    name = "yahoo"

    def get_daily_prices(
        self,
        symbols: list[str],
        start: date,
        end: date,
    ) -> pl.DataFrame:
        """
        Download daily prices from Yahoo Finance using yfinance.

        The returned data is provider-shaped, not yet canonical.
        Standardization happens later in validation.py.
        """

        if not symbols:
            raise ValueError("No symbols provided.")

        if start > end:
            raise ValueError("Start date must be before end date.")

        ingested_at = datetime.now(timezone.utc)

        frames: list[pd.DataFrame] = []

        for symbol in symbols:
            provider_symbol = symbol.upper()
            canonical_symbol = symbol.upper()

            df = yf.download(
                tickers=provider_symbol,
                start=start,
                end=end,
                interval="1d",
                auto_adjust=False,
                progress=False,
            )

            if df.empty:
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [
                    col[0] if isinstance(col, tuple) else col
                    for col in df.columns
                ]

            df = df.reset_index()

            df["symbol"] = canonical_symbol
            df["provider"] = self.name
            df["ingested_at"] = ingested_at

            frames.append(df)

        if not frames:
            return pl.DataFrame()

        prices = pd.concat(frames, ignore_index=True)

        return pl.from_pandas(prices)