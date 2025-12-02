"""In-memory paper broker for simulating order flow.

This lightweight broker is intended for local development and unit tests.
It keeps prices and positions in memory and immediately "fills" market orders
at the requested symbol's last price.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Mapping

from trading_bot.brokers.base import BrokerClient
from trading_bot.models.types import BrokerPrices, Order, OrderRequest, Position


@dataclass
class PaperBroker(BrokerClient):
    """Simple paper broker with pluggable price snapshots."""

    prices: BrokerPrices = field(default_factory=dict)
    positions: dict[str, Position] = field(default_factory=dict)

    def update_prices(self, prices: BrokerPrices) -> None:
        """Replace the internal price map used for fills."""

        self.prices = dict(prices)

    def get_prices(self, symbols: Iterable[str]) -> BrokerPrices:
        return {symbol: self.prices.get(symbol, 0.0) for symbol in symbols}

    def place_order(self, order: OrderRequest) -> Order:
        price = self.prices.get(order.symbol)
        if price is None:
            raise ValueError(f"Price for {order.symbol} not available")

        position = self.positions.get(order.symbol)
        signed_qty = order.quantity if order.side.value == "BUY" else -order.quantity
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
            id=f"paper-{order.symbol}-{datetime.utcnow().timestamp()}",
            request=order,
            status="filled",
            filled_quantity=order.quantity,
        )

    def cancel_order(self, order_id: str) -> None:  # noqa: ARG002
        # Nothing to cancel in the immediate-fill paper broker.
        return None

    def get_positions(self) -> Mapping[str, Position]:
        return dict(self.positions)
