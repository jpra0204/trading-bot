"""Execution loop tying together strategy and broker."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from trading_bot.brokers.base import BrokerClient
from trading_bot.config.schemas import TradingBotConfig
from trading_bot.models.types import OrderRequest
from trading_bot.strategies.base import Strategy


@dataclass
class Runner:
    """Minimal runner that pulls prices, gets orders, and forwards them to a broker."""

    config: TradingBotConfig
    strategy: Strategy
    broker: BrokerClient

    def run_step(self) -> list[str]:
        symbols = {symbol for pair in self.config.pairs for symbol in (pair.symbol_a, pair.symbol_b)}
        prices = self.broker.get_prices(symbols)
        orders: Iterable[OrderRequest] = self.strategy.evaluate(prices)
        confirmations: list[str] = []
        for order in orders:
            ack = self.broker.place_order(order)
            confirmations.append(ack.id)
        return confirmations
