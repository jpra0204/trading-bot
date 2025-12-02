"""PnL and accounting utilities for backtests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from trading_bot.models.types import BrokerPrices, Position


@dataclass
class AccountSnapshot:
    """Represents a simple marked-to-market account state."""

    equity: float
    positions: Mapping[str, Position]


def mark_to_market(prices: BrokerPrices, positions: Mapping[str, Position]) -> AccountSnapshot:
    """Compute account equity using latest prices."""

    equity = sum(position.quantity * prices.get(symbol, 0.0) for symbol, position in positions.items())
    return AccountSnapshot(equity=equity, positions=dict(positions))
