"""In-memory paper broker for simple testing and dry-runs.

The paper broker maintains cash, positions, and orders in memory and fills
market orders immediately at the current price sourced from either a user
provided ``price_feed`` callable or an internally managed last-price map.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable

from trading_bot.brokers.base import BrokerClient, BrokerError
from trading_bot.models.types import Bar, Order, OrderType, Position, Quote, Side


class PaperBrokerClient(BrokerClient):
    """Lightweight paper broker that fills market orders at the current price."""

    def __init__(self, starting_cash: float = 100_000, price_feed: Callable[[str], float] | None = None) -> None:
        self.cash: float = float(starting_cash)
        self.price_feed = price_feed
        self._positions: dict[str, Position] = {}
        self._orders: dict[str, Order] = {}
        self._last_price: dict[str, float] = {}
        self._order_seq: int = 1

    # Price helpers -----------------------------------------------------
    def set_price(self, symbol: str, price: float) -> None:
        """Set the latest price for a symbol when no external feed is provided."""

        self._last_price[symbol] = float(price)

    def _resolve_price(self, symbol: str) -> float:
        if self.price_feed is not None:
            price = self.price_feed(symbol)
            if price is None:
                raise BrokerError(f"Price feed did not return a price for {symbol}")
            return float(price)

        if symbol not in self._last_price:
            raise BrokerError(f"No price available for symbol {symbol}")
        return self._last_price[symbol]

    # BrokerClient interface -------------------------------------------
    def get_quote(self, symbol: str) -> Quote:
        price = self._resolve_price(symbol)
        return Quote(symbol=symbol, bid=None, ask=None, last=price, timestamp=datetime.utcnow())

    def get_latest_bar(self, symbol: str, interval: str = "1min") -> Bar:  # noqa: ARG002
        price = self._resolve_price(symbol)
        return Bar(
            symbol=symbol,
            open=price,
            high=price,
            low=price,
            close=price,
            volume=0.0,
            timestamp=datetime.utcnow(),
        )

    def get_historical_bars(self, symbol: str, limit: int, interval: str = "1min") -> list[Bar]:  # noqa: ARG002
        price = self._resolve_price(symbol)
        now = datetime.utcnow()
        return [
            Bar(
                symbol=symbol,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=0.0,
                timestamp=now - timedelta(minutes=i),
            )
            for i in range(limit)
        ]

    def get_positions(self) -> dict[str, Position]:
        return dict(self._positions)

    def get_position(self, symbol: str) -> Position | None:
        return self._positions.get(symbol)

    def place_order(
        self,
        symbol: str,
        side: Side,
        quantity: float,
        order_type: OrderType = "market",
        limit_price: float | None = None,
    ) -> Order:
        if order_type == "limit":
            raise NotImplementedError("Limit orders are not yet supported in PaperBrokerClient")

        price = self._resolve_price(symbol)
        timestamp = datetime.utcnow()
        order_id = f"paper-{self._order_seq}"
        self._order_seq += 1

        signed_qty = quantity if side == "buy" else -quantity
        existing = self._positions.get(symbol)
        prev_qty = existing.quantity if existing else 0.0
        prev_avg = existing.avg_price if existing else 0.0
        new_qty = prev_qty + signed_qty

        if new_qty != 0:
            new_avg = ((prev_qty * prev_avg) + (signed_qty * price)) / new_qty
        else:
            new_avg = price

        self._positions[symbol] = Position(symbol=symbol, quantity=new_qty, avg_price=new_avg)

        cash_delta = -quantity * price if side == "buy" else quantity * price
        self.cash += cash_delta

        order = Order(
            id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            timestamp=timestamp,
            status="filled",
        )
        self._orders[order_id] = order
        return order

    def cancel_order(self, order_id: str) -> None:
        order = self._orders.get(order_id)
        if order is None:
            raise BrokerError(f"Order {order_id} not found")
        if order.status == "filled":
            raise BrokerError("Cannot cancel a filled order")

        self._orders[order_id] = order.model_copy(update={"status": "canceled"})

    def get_open_orders(self) -> list[Order]:
        return [order for order in self._orders.values() if order.status not in {"filled", "canceled"}]

    def get_account_balance(self) -> float:
        """Return current cash balance (equity calculation can be added later)."""

        return self.cash
