"""Backtest broker implementation that replays historical OHLCV bars."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from trading_bot.brokers.base import BrokerClient, BrokerError
from trading_bot.models.types import Bar, Order, OrderType, Position, Quote, Side


@dataclass
class BacktestBroker(BrokerClient):
    """Simple in-memory broker for backtesting with bar data."""

    bars_by_symbol: dict[str, list[Bar]]
    starting_cash: float = 100_000.0
    positions: dict[str, Position] = field(default_factory=dict)
    cash: float = field(init=False)
    current_index: int = field(default=-1, init=False)
    _order_history: list[Order] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if not self.bars_by_symbol:
            raise BrokerError("No bar data provided to backtest broker")
        self.cash = float(self.starting_cash)
        self._max_bars = min(len(bars) for bars in self.bars_by_symbol.values())
        if self._max_bars == 0:
            raise BrokerError("Bar data is empty for provided symbols")

    def step(self) -> int:
        """Advance to the next bar for all symbols."""

        next_index = self.current_index + 1
        if next_index >= self._max_bars:
            raise StopIteration("No more bars available in backtest data")
        self.current_index = next_index
        return self.current_index

    def _get_bar(self, symbol: str, index: int) -> Bar:
        bars = self.bars_by_symbol.get(symbol)
        if bars is None:
            raise BrokerError(f"No bars loaded for symbol {symbol}")
        if index < 0 or index >= len(bars):
            raise BrokerError(f"Bar index {index} out of range for {symbol}")
        return bars[index]

    def get_latest_bar(self, symbol: str, interval: str = "1min") -> Bar:  # noqa: ARG002
        if self.current_index < 0:
            raise BrokerError("Backtest has not been started; call step() first")
        return self._get_bar(symbol, self.current_index)

    def get_historical_bars(self, symbol: str, limit: int, interval: str = "1min") -> list[Bar]:  # noqa: ARG002
        if self.current_index < 0:
            raise BrokerError("Backtest has not been started; call step() first")
        end = self.current_index + 1
        start = max(0, end - limit)
        bars = self.bars_by_symbol.get(symbol)
        if bars is None:
            raise BrokerError(f"No bars loaded for symbol {symbol}")
        return bars[start:end]

    def get_quote(self, symbol: str) -> Quote:
        bar = self.get_latest_bar(symbol)
        return Quote(symbol=symbol, bid=None, ask=None, last=bar.close, timestamp=bar.timestamp)

    def get_positions(self) -> Mapping[str, Position]:
        return dict(self.positions)

    def get_position(self, symbol: str) -> Position | None:
        return self.positions.get(symbol)

    def get_account_balance(self) -> float:
        return float(self.cash)

    def get_open_orders(self) -> list[Order]:
        return []

    def place_order(
        self,
        symbol: str,
        side: Side,
        quantity: float,
        order_type: OrderType = "market",
        limit_price: float | None = None,
    ) -> Order:
        if quantity <= 0:
            raise BrokerError("Order quantity must be positive")
        if self.current_index < 0:
            raise BrokerError("Backtest has not been started; call step() first")

        bar = self.get_latest_bar(symbol)
        fill_price = bar.close if order_type == "market" or limit_price is None else limit_price

        signed_qty = quantity if side == "buy" else -quantity
        position = self.positions.get(symbol)
        if position is None:
            if signed_qty != 0:
                self.positions[symbol] = Position(symbol=symbol, quantity=signed_qty, avg_price=fill_price)
        else:
            new_qty = position.quantity + signed_qty
            if new_qty == 0:
                del self.positions[symbol]
            else:
                avg_price = (position.quantity * position.avg_price + signed_qty * fill_price) / new_qty
                self.positions[symbol] = Position(symbol=symbol, quantity=new_qty, avg_price=avg_price)

        self.cash -= signed_qty * fill_price

        order = Order(
            id=f"order-{len(self._order_history) + 1}",
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=fill_price,
            timestamp=bar.timestamp,
            status="filled",
        )
        self._order_history.append(order)
        return order

    def cancel_order(self, order_id: str) -> None:  # noqa: ARG002
        return None

    @property
    def order_history(self) -> list[Order]:
        return list(self._order_history)
