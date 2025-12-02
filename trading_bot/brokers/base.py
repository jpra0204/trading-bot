"""Abstract broker client interface for trading operations.

This module defines the minimal set of methods a broker implementation must
provide so that strategies can request prices, submit and manage orders, and
inspect account state without coupling to a specific API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping

from trading_bot.models.types import Bar, Order, OrderType, Position, Quote, Side


class BrokerError(Exception):
    """Represents errors raised by broker implementations."""


class BrokerClient(ABC):
    """Common interface that all broker clients must implement."""

    @abstractmethod
    def get_quote(self, symbol: str) -> Quote:
        """Return the latest quote for the given symbol."""

    @abstractmethod
    def get_latest_bar(self, symbol: str, interval: str = "1min") -> Bar:
        """Return the most recent bar for the symbol at the specified interval."""

    @abstractmethod
    def get_historical_bars(self, symbol: str, limit: int, interval: str = "1min") -> list[Bar]:
        """Return a list of the latest ``limit`` bars for the symbol."""

    @abstractmethod
    def get_positions(self) -> Mapping[str, Position]:
        """Return a mapping of current positions keyed by symbol."""

    @abstractmethod
    def get_position(self, symbol: str) -> Position | None:
        """Return the current position for ``symbol`` if it exists."""

    @abstractmethod
    def place_order(
        self,
        symbol: str,
        side: Side,
        quantity: float,
        order_type: OrderType = "market",
        limit_price: float | None = None,
    ) -> Order:
        """Submit an order for the given symbol.

        Quantities are expressed in shares. Prices are expressed in the quote
        currency of the symbol. Implementations should raise ``BrokerError`` if
        an order cannot be placed (e.g., missing prices or unsupported type).
        """

    @abstractmethod
    def cancel_order(self, order_id: str) -> None:
        """Cancel a previously submitted order if it is still open."""

    @abstractmethod
    def get_open_orders(self) -> list[Order]:
        """Return all currently open (not filled or canceled) orders."""

    @abstractmethod
    def get_account_balance(self) -> float:
        """Return the current account cash or equity balance."""
