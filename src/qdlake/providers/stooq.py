from datetime import date, datetime, timezone

import pandas as pd
import polars as pl
from pandas_datareader.stooq import StooqDailyReader

from qdlake.providers.base import PriceProvider


class StooqProvider(PriceProvider):
    name = "stooq"

    def get_daily_prices(
        self,
        symbols: list[str],
        start: date,
        end: date,
    ) -> pl.DataFrame:
        """
        Download daily prices from Stooq for the given symbols and date range.

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
            provider_symbol = symbol.lower()
            canonical_symbol = symbol.upper()

            reader = StooqDailyReader(
                symbols=provider_symbol,
                start=start,
                end=end,
            )

            df = reader.read()

            if df.empty:
                continue

            df = df.reset_index()

            df["symbol"] = canonical_symbol
            df["provider"] = self.name
            df["ingested_at"] = ingested_at

            frames.append(df)

        if not frames:
            return pl.DataFrame()

        prices = pd.concat(frames, ignore_index=True)

        return pl.from_pandas(prices)