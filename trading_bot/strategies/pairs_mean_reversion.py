"""Mean-reversion pairs trading strategy scaffold."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from trading_bot.config.schemas import PairConfig
from trading_bot.models.types import BrokerPrices, OrderRequest
from trading_bot.strategies.base import Strategy


@dataclass
class PairsMeanReversionStrategy(Strategy):
    """Placeholder mean-reversion strategy (logic to be implemented)."""

    pairs: Sequence[PairConfig]

    def evaluate(self, prices: BrokerPrices) -> Iterable[OrderRequest]:
        """Placeholder evaluate hook; to be implemented with trading logic."""

        raise NotImplementedError("PairsMeanReversionStrategy.evaluate is not implemented yet")
