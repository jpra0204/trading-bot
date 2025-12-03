"""Smoke tests for the trading runner wiring strategy and broker."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from trading_bot.brokers.paper import PaperBrokerClient
from trading_bot.config.schemas import PairConfig, RiskConfig, RunConfig
from trading_bot.execution.runner import TradingRunner
from trading_bot.models.types import Bar


def _stub_bars(values: dict[str, list[float]]):
    def _factory(symbol: str, limit: int, interval: str = "1min") -> list[Bar]:  # noqa: ARG001
        series = values[symbol][:limit]
        now = datetime.utcnow()
        return [
            Bar(
                symbol=symbol,
                open=v,
                high=v,
                low=v,
                close=v,
                volume=0.0,
                timestamp=now - timedelta(minutes=i),
            )
            for i, v in enumerate(series)
        ]

    return _factory


def _build_config() -> RunConfig:
    pair = PairConfig(
        name="TEST",
        symbol_long="AAA",
        symbol_short="BBB",
        lookback_bars=3,
        entry_zscore=1.0,
        exit_zscore=0.5,
        max_holding_bars=5,
        notional_per_leg=500.0,
    )
    risk = RiskConfig(
        max_total_notional=10_000,
        max_pairs_open=1,
        max_daily_loss=1_000,
        max_position_per_symbol=5_000,
    )
    return RunConfig(mode="paper", poll_interval_seconds=1, pairs=[pair], risk=risk)


def test_runner_executes_without_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _build_config()
    broker = PaperBrokerClient(starting_cash=10_000)

    broker.set_price("AAA", 110.0)
    broker.set_price("BBB", 90.0)

    stub = _stub_bars({"AAA": [11.0, 12.0, 13.0], "BBB": [10.0, 10.0, 10.0]})
    monkeypatch.setattr(broker, "get_historical_bars", stub)

    runner = TradingRunner(config=config, broker=broker)

    runner.run_once()
    state = runner._states["TEST"]
    assert state.is_open is True

    runner.run_once()
    state = runner._states["TEST"]
    assert state.bars_held >= 1

    pos_long = broker.get_position("AAA")
    pos_short = broker.get_position("BBB")
    assert pos_long is not None and pos_long.quantity != 0
    assert pos_short is not None and pos_short.quantity != 0
