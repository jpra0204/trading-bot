"""Math helpers for spread calculations and z-scores."""

from __future__ import annotations

from collections import deque
from typing import Deque, Iterable

from trading_bot.config.schemas import PairConfig
from trading_bot.models.types import BrokerPrices


def pair_spread(prices: BrokerPrices, pair: PairConfig) -> float:
    """Compute the simple price spread for a pair."""

    price_a = prices.get(pair.symbol_a)
    price_b = prices.get(pair.symbol_b)
    if price_a is None or price_b is None:
        raise ValueError(f"Missing prices for pair {pair.symbol_a}/{pair.symbol_b}")
    hedge_ratio = pair.hedge_ratio or 1.0
    return price_a - hedge_ratio * price_b


def zscore(latest_value: float, history: Iterable[float] | None = None, lookback: int = 30) -> float | None:
    """Calculate a basic z-score given a history of spread values.

    The helper is intentionally minimal for the scaffold: when there is no
    history, the function returns ``None`` so callers can skip trading until
    sufficient context is available.
    """

    values: Deque[float] = deque(history or [], maxlen=lookback)
    values.append(latest_value)
    if len(values) < lookback:
        return None

    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = variance ** 0.5
    if std == 0:
        return 0.0
    return (latest_value - mean) / std
