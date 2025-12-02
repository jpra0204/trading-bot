"""Risk sizing helpers for the trading bot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from trading_bot.models.types import BrokerPrices, OrderRequest


@dataclass
class RiskManager:
    """Evaluates whether proposed orders fit risk constraints."""

    max_notional: float

    def validate(self, prices: BrokerPrices, orders: Mapping[str, OrderRequest]) -> bool:
        notional = 0.0
        for order in orders.values():
            price = prices.get(order.symbol, 0.0)
            notional += abs(price * order.quantity)
        return notional <= self.max_notional
