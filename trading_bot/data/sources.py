"""Interfaces and helpers for retrieving market data."""

from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, Mapping
from zoneinfo import ZoneInfo

from trading_bot.models.types import Bar, BrokerPrices


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


def load_bars_from_csv(
    path: str | Path,
    symbol: str,
    timestamp_col: str = "timestamp",
    open_col: str = "open",
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    volume_col: str = "volume",
    tz: str | None = None,
) -> list[Bar]:
    """Load OHLCV bars for a symbol from a CSV file.

    The CSV is expected to contain a header row with timestamp and OHLCV columns.
    Column names can be customized via parameters. ``timestamp_col`` should hold
    ISO-8601 compatible strings; if ``tz`` is provided, timestamps will be
    converted to that timezone (or annotated if naïve). All price and volume
    columns are parsed as floats.

    Args:
        path: Path to the CSV file.
        symbol: Symbol to assign to each bar.
        timestamp_col: Column containing timestamps.
        open_col: Column containing open prices.
        high_col: Column containing high prices.
        low_col: Column containing low prices.
        close_col: Column containing close prices.
        volume_col: Column containing volume values.
        tz: Optional timezone string (e.g., ``"UTC"``) to apply to timestamps.

    Returns:
        A list of :class:`trading_bot.models.types.Bar` sorted by timestamp.

    Raises:
        ValueError: If required columns are missing or timestamps cannot be parsed.
    """

    csv_path = Path(path)
    bars: list[Bar] = []
    tzinfo = ZoneInfo(tz) if tz else None

    with csv_path.open(newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError("CSV file is missing a header row")

        required = [timestamp_col, open_col, high_col, low_col, close_col, volume_col]
        missing = [column for column in required if column not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV missing required columns: {', '.join(missing)}")

        for row in reader:
            try:
                timestamp = datetime.fromisoformat(row[timestamp_col])
            except Exception as exc:  # noqa: BLE001
                raise ValueError(f"Invalid timestamp value: {row[timestamp_col]!r}") from exc

            if tzinfo:
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=tzinfo)
                else:
                    timestamp = timestamp.astimezone(tzinfo)

            try:
                open_price = float(row[open_col])
                high_price = float(row[high_col])
                low_price = float(row[low_col])
                close_price = float(row[close_col])
                volume = float(row[volume_col])
            except Exception as exc:  # noqa: BLE001
                raise ValueError(f"Failed to parse OHLCV values for row {row}") from exc

            bars.append(
                Bar(
                    symbol=symbol,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=volume,
                    timestamp=timestamp,
                )
            )

    bars.sort(key=lambda bar: bar.timestamp)
    return bars


def load_bars_for_symbols_from_csv(mapping: dict[str, str | Path], **kwargs: object) -> dict[str, list[Bar]]:
    """Load bars for multiple symbols from a mapping of CSV paths.

    Args:
        mapping: Dictionary of ``symbol -> csv_path`` entries.
        **kwargs: Additional keyword arguments forwarded to :func:`load_bars_from_csv`.

    Returns:
        Mapping of symbols to their loaded bar lists.
    """

    return {symbol: load_bars_from_csv(path, symbol, **kwargs) for symbol, path in mapping.items()}
