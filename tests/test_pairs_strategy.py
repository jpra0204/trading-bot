"""Tests for the mean-reversion pairs strategy."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from trading_bot.brokers.paper import PaperBrokerClient
from trading_bot.config.schemas import PairConfig, RiskConfig
from trading_bot.models.types import Bar
from trading_bot.strategies.base import Signal
from trading_bot.strategies.pairs_mean_reversion import PairState, PairsMeanReversionStrategy


def _bars(values: list[float], symbol: str) -> list[Bar]:
    now = datetime.utcnow()
    return [
        Bar(symbol=symbol, open=v, high=v, low=v, close=v, volume=0.0, timestamp=now - timedelta(minutes=i))
        for i, v in enumerate(values)
    ]


def _configs() -> tuple[PairConfig, RiskConfig]:
    pair = PairConfig(
        name="TEST",
        symbol_long="AAA",
        symbol_short="BBB",
        lookback_bars=3,
        entry_zscore=1.0,
        exit_zscore=0.5,
        max_holding_bars=5,
        notional_per_leg=1000.0,
    )
    risk = RiskConfig(
        max_total_notional=100_000,
        max_pairs_open=2,
        max_daily_loss=10_000,
        max_position_per_symbol=50_000,
    )
    return pair, risk


def test_compute_spread_and_zscore() -> None:
    pair_config, risk_config = _configs()
    broker = PaperBrokerClient()
    strategy = PairsMeanReversionStrategy(pair_config, risk_config, broker)

    long_values = [11.0, 12.0, 13.0]
    short_values = [10.0, 10.0, 10.0]

    def stub_get_historical(symbol: str, limit: int, interval: str = "1min") -> list[Bar]:  # noqa: ARG001
        return _bars(long_values if symbol == "AAA" else short_values, symbol)

    broker.get_historical_bars = stub_get_historical  # type: ignore[assignment]

    spread, z = strategy.compute_spread_and_zscore()
    assert pytest.approx(spread) == 3.0
    assert z > 1.0


def test_generate_signals_based_on_zscore() -> None:
    pair_config, risk_config = _configs()
    broker = PaperBrokerClient()
    strategy = PairsMeanReversionStrategy(pair_config, risk_config, broker)
    state = PairState()

    def stub(symbol: str, limit: int, interval: str = "1min") -> list[Bar]:  # noqa: ARG001
        values = {"AAA": [11.0, 12.0, 13.0], "BBB": [10.0, 10.0, 10.0]}
        return _bars(values[symbol], symbol)

    broker.get_historical_bars = stub  # type: ignore[assignment]
    assert strategy.generate_signal(state) == Signal.ENTER_SHORT_LONG

    def stub_negative(symbol: str, limit: int, interval: str = "1min") -> list[Bar]:  # noqa: ARG001
        values = {"AAA": [9.0, 8.5, 7.0], "BBB": [10.0, 10.0, 10.0]}
        return _bars(values[symbol], symbol)

    broker.get_historical_bars = stub_negative  # type: ignore[assignment]
    state.is_open = False
    assert strategy.generate_signal(state) == Signal.ENTER_LONG_SHORT

    def stub_flat(symbol: str, limit: int, interval: str = "1min") -> list[Bar]:  # noqa: ARG001
        values = {"AAA": [10.0, 10.0, 10.0], "BBB": [10.0, 10.0, 10.0]}
        return _bars(values[symbol], symbol)

    broker.get_historical_bars = stub_flat  # type: ignore[assignment]
    state.is_open = False
    assert strategy.generate_signal(state) == Signal.HOLD


def test_generate_signal_exit_on_hold_period() -> None:
    pair_config, risk_config = _configs()
    broker = PaperBrokerClient()
    strategy = PairsMeanReversionStrategy(pair_config, risk_config, broker)
    state = PairState(is_open=True, bars_held=pair_config.max_holding_bars)

    def stub_flat(symbol: str, limit: int, interval: str = "1min") -> list[Bar]:  # noqa: ARG001
        values = {"AAA": [10.0, 10.0, 10.0], "BBB": [10.0, 10.0, 10.0]}
        return _bars(values[symbol], symbol)

    broker.get_historical_bars = stub_flat  # type: ignore[assignment]
    assert strategy.generate_signal(state) == Signal.EXIT


def test_execute_enters_and_exits_positions() -> None:
    pair_config, risk_config = _configs()
    broker = PaperBrokerClient()
    strategy = PairsMeanReversionStrategy(pair_config, risk_config, broker)
    state = PairState()

    # Provide prices for sizing and synthetic history for signal generation
    broker.set_price("AAA", 100.0)
    broker.set_price("BBB", 50.0)

    def stub(symbol: str, limit: int, interval: str = "1min") -> list[Bar]:  # noqa: ARG001
        values = {"AAA": [12.0, 11.0, 9.0], "BBB": [10.0, 10.0, 10.0]}
        return _bars(values[symbol], symbol)

    broker.get_historical_bars = stub  # type: ignore[assignment]
    signal = strategy.generate_signal(state)
    strategy.execute(signal, state)

    pos_long = broker.get_position("AAA")
    pos_short = broker.get_position("BBB")
    assert pos_long is not None and pos_short is not None
    if signal == Signal.ENTER_LONG_SHORT:
        assert pos_long.quantity > 0
        assert pos_short.quantity < 0
    elif signal == Signal.ENTER_SHORT_LONG:
        assert pos_long.quantity < 0
        assert pos_short.quantity > 0
    assert state.is_open is True

    exit_signal = Signal.EXIT
    strategy.execute(exit_signal, state)
    pos_long = broker.get_position("AAA")
    pos_short = broker.get_position("BBB")
    assert pos_long is None or pos_long.quantity == 0
    assert pos_short is None or pos_short.quantity == 0
    assert state.is_open is False

