"""Typed domain models for quotes, bars, orders, and positions."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict

Side = Literal["buy", "sell"]
OrderType = Literal["market", "limit"]


BrokerPrices = Mapping[str, float]


class Quote(BaseModel):
    """Represents the latest top-of-book quote for a tradable symbol."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    bid: float | None = None
    ask: float | None = None
    last: float
    timestamp: datetime


class Bar(BaseModel):
    """OHLCV bar (candle) for a symbol at a specific timestamp."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime


class Order(BaseModel):
    """Represents a placed order and its latest status."""

    model_config = ConfigDict(frozen=True)

    id: str
    symbol: str
    side: Side
    order_type: OrderType
    quantity: float
    price: float | None = None
    timestamp: datetime
    status: Literal["new", "filled", "partially_filled", "canceled"]


class OrderRequest(BaseModel):
    """Lightweight order intent used when submitting to a broker."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    side: Side
    order_type: OrderType = "market"
    quantity: float
    price: float | None = None


class Position(BaseModel):
    """Tracks an open position and its average cost."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    quantity: float
    avg_price: float
    unrealized_pnl: float | None = None
