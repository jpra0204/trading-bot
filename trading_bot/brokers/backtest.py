"""Backtest broker that replays historical prices.

This broker reads prices from a user-provided iterator or mapping, making it
simple to plug in CSV readers or synthetic data streams for tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Mapping

from trading_bot.brokers.base import BrokerClient
from trading_bot.models.types import BrokerPrices, Order, OrderRequest, Position


@dataclass
class BacktestBroker(BrokerClient):
    """Broker that pulls prices from a deterministic source during backtests."""

    price_feed: Iterator[BrokerPrices] | None = None
    positions: dict[str, Position] = field(default_factory=dict)
    _latest_prices: BrokerPrices = field(default_factory=dict)

    def step_prices(self) -> BrokerPrices:
        """Advance the iterator and capture the latest prices."""

        if self.price_feed is None:
            raise RuntimeError("No price feed provided for backtest broker")
        self._latest_prices = next(self.price_feed)
        return self._latest_prices

    def get_prices(self, symbols: Iterable[str]) -> BrokerPrices:
        prices = self._latest_prices or {}
        return {symbol: prices.get(symbol, 0.0) for symbol in symbols}

    def place_order(self, order: OrderRequest) -> Order:
        price = self._latest_prices.get(order.symbol)
        if price is None:
            raise ValueError(f"Price for {order.symbol} not available in feed")

        signed_qty = order.quantity if order.side.value == "BUY" else -order.quantity
        position = self.positions.get(order.symbol)
        if position:
            total_qty = position.quantity + signed_qty
            new_avg = (
                (position.quantity * position.avg_price) + (signed_qty * price)
            ) / total_qty if total_qty else position.avg_price
            self.positions[order.symbol] = Position(
                symbol=order.symbol,
                quantity=total_qty,
                avg_price=new_avg,
            )
        else:
            self.positions[order.symbol] = Position(
                symbol=order.symbol,
                quantity=signed_qty,
                avg_price=price,
            )

        return Order(
            id=f"backtest-{order.symbol}-{len(self.positions)}",
            request=order,
            status="filled",
            filled_quantity=order.quantity,
        )

    def cancel_order(self, order_id: str) -> None:  # noqa: ARG002
        return None

    def get_positions(self) -> Mapping[str, Position]:
        return dict(self.positions)
