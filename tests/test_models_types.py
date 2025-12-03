"""Tests for typed domain models."""

from datetime import datetime, timezone

from trading_bot.models.types import Bar, Order, Quote


def test_quote_and_bar_construction() -> None:
    timestamp = datetime.now(tz=timezone.utc)
    quote = Quote(symbol="AAPL", bid=189.5, ask=190.0, last=189.8, timestamp=timestamp)
    bar = Bar(
        symbol="AAPL",
        open=189.0,
        high=191.0,
        low=188.5,
        close=190.5,
        volume=1_000_000,
        timestamp=timestamp,
    )

    assert quote.symbol == "AAPL"
    assert bar.close == 190.5


def test_order_fields() -> None:
    timestamp = datetime.now(tz=timezone.utc)
    order = Order(
        id="abc123",
        symbol="AAPL",
        side="buy",
        order_type="limit",
        quantity=10,
        price=189.5,
        timestamp=timestamp,
        status="new",
    )

    assert order.side == "buy"
    assert order.order_type == "limit"
