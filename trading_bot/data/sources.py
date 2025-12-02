"""Interfaces and helpers for retrieving market data."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, Iterator, Mapping

from trading_bot.models.types import BrokerPrices


class DataSource(ABC):
    """Abstract source capable of yielding price snapshots."""

    @abstractmethod
    def stream_prices(self, symbols: Iterable[str]) -> Iterator[BrokerPrices]:
        """Yield successive price dictionaries for the given symbols."""


class CsvBarSource(DataSource):
    """Placeholder CSV loader for backtests.

    This stub illustrates how a concrete data source might be structured; the
    implementation can be expanded to parse timestamps and OHLCV data.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def stream_prices(self, symbols: Iterable[str]) -> Iterator[BrokerPrices]:  # noqa: D401
        for symbol in symbols:
            # Placeholder: yield a single static price for scaffolding purposes.
            yield {symbol: 100.0}
