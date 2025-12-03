"""Backtest engine for running pairs trading simulations."""

from __future__ import annotations

from dataclasses import dataclass

from trading_bot.brokers.backtest import BacktestBroker
from trading_bot.config.schemas import PairConfig, RiskConfig
from trading_bot.models.types import Bar, Order
from trading_bot.strategies.base import Signal
from trading_bot.strategies.pairs_mean_reversion import PairState, PairsMeanReversionStrategy


@dataclass
class BacktestResult:
    starting_equity: float
    ending_equity: float
    total_return_pct: float
    max_drawdown_pct: float
    trades: list[Order]


def _compute_equity(broker: BacktestBroker) -> float:
    positions = broker.get_positions()
    equity = broker.get_account_balance()
    for symbol, position in positions.items():
        bar = broker.get_latest_bar(symbol)
        equity += position.quantity * bar.close
    return equity


def _max_drawdown_pct(equity_curve: list[float]) -> float:
    peak = equity_curve[0]
    max_drawdown = 0.0
    for value in equity_curve:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak * 100 if peak else 0.0
        max_drawdown = max(max_drawdown, drawdown)
    return max_drawdown


def run_pairs_backtest(
    pair_config: PairConfig,
    risk_config: RiskConfig,
    bars_by_symbol: dict[str, list[Bar]],
    starting_cash: float = 100_000.0,
) -> BacktestResult:
    """Run a simple backtest for the pairs mean-reversion strategy."""

    required_symbols = {pair_config.symbol_long, pair_config.symbol_short}
    missing = required_symbols.difference(bars_by_symbol)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Missing bar data for symbols: {missing_list}")

    broker = BacktestBroker(bars_by_symbol=bars_by_symbol, starting_cash=starting_cash)
    strategy = PairsMeanReversionStrategy(pair_config, risk_config, broker)
    state = PairState()

    bar_count = min(len(bars_by_symbol[pair_config.symbol_long]), len(bars_by_symbol[pair_config.symbol_short]))
    equity_curve = [starting_cash]

    for _ in range(bar_count):
        try:
            broker.step()
        except StopIteration:
            break

        if broker.current_index + 1 < pair_config.lookback_bars:
            equity_curve.append(_compute_equity(broker))
            continue

        signal = strategy.generate_signal(state)
        if signal != Signal.HOLD:
            strategy.execute(signal, state)

        equity_curve.append(_compute_equity(broker))

    starting_equity = starting_cash
    ending_equity = equity_curve[-1]
    total_return_pct = (ending_equity / starting_equity - 1) * 100 if starting_equity else 0.0
    max_drawdown_pct = _max_drawdown_pct(equity_curve)
    trades = broker.order_history

    return BacktestResult(
        starting_equity=starting_equity,
        ending_equity=ending_equity,
        total_return_pct=total_return_pct,
        max_drawdown_pct=max_drawdown_pct,
        trades=trades,
    )
