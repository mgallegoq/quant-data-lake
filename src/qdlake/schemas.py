from datetime import date, datetime, timezone

from pydantic import BaseModel, Field


class DailyPriceBar(BaseModel):
    symbol: str = Field(min_length=1, description="The stock symbol")
    date: datetime = Field(description="The date of the price bar")

    open: float = Field(gt=0, description="The opening price")
    high: float = Field(gt=0, description="The highest price")
    low: float = Field(gt=0, description="The lowest price")
    close: float = Field(gt=0, description="The closing price")

    volume: int = Field(ge=0, description="The trading volume")
    provider: str = Field(min_length=1, description="The data provider")
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="The timestamp when the data was ingested",
    )