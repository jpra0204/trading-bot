"""Strategy interfaces and concrete implementations."""

from trading_bot.strategies.base import Strategy
from trading_bot.strategies.pairs_mean_reversion import PairsMeanReversionStrategy

__all__ = ["Strategy", "PairsMeanReversionStrategy"]
