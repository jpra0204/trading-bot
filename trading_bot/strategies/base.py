"""Base interfaces for trading strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from trading_bot.models.types import BrokerPrices, OrderRequest


class Strategy(ABC):
    """Strategy interface that transforms prices into orders."""

    @abstractmethod
    def evaluate(self, prices: BrokerPrices) -> Iterable[OrderRequest]:
        """Return zero or more orders based on the latest prices."""
