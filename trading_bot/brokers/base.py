"""Abstract broker client interface.

The broker layer hides the mechanics of sending orders and fetching prices
so strategies can operate against a simple API. Concrete implementations can
wrap live APIs, paper trading engines, or backtest data feeds.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Mapping

from trading_bot.models.types import BrokerPrices, Order, OrderRequest, Position


class BrokerClient(ABC):
    """Common interface that all broker clients must implement."""

    @abstractmethod
    def get_prices(self, symbols: Iterable[str]) -> BrokerPrices:
        """Return the latest prices for each symbol."""

    @abstractmethod
    def place_order(self, order: OrderRequest) -> Order:
        """Submit an order and return an acknowledgement."""

    @abstractmethod
    def cancel_order(self, order_id: str) -> None:
        """Cancel an existing order if supported."""

    @abstractmethod
    def get_positions(self) -> Mapping[str, Position]:
        """Return current open positions keyed by symbol."""
