from abc import ABC, abstractmethod
from datetime import date

import polars as pl


class PriceProvider(ABC):
    """
    Abstract interface for daily price providers.

    Any concrete provider must expose a name and implement
    get_daily_prices with the same signature.
    """

    name: str

    @abstractmethod
    def get_daily_prices(
        self,
        symbols: list[str],
        start: date,
        end: date,
    ) -> pl.DataFrame:
        """
        Return daily OHLCV data for the requested symbols and date range.

        The returned DataFrame may still use provider-specific column names.
        Standardization happens later in validation.py.
        """
        raise NotImplementedError("Subclasses must implement this method")