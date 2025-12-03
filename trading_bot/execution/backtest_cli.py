"""Simple CLI for running pairs backtests from CSV files."""

from __future__ import annotations

import argparse
from collections.abc import Mapping

from trading_bot.config.schemas import PairConfig, RiskConfig
from trading_bot.data.sources import load_bars_for_symbols_from_csv
from trading_bot.execution.backtest import run_pairs_backtest


def _get_field(result: object, name: str) -> float | int | object:
    if isinstance(result, Mapping):
        return result[name]
    return getattr(result, name)


def main() -> None:
    """Entry point for running a single pairs backtest from CSV files."""

    parser = argparse.ArgumentParser(description="Run a pairs backtest from CSV data")
    parser.add_argument("--long-symbol", required=True, help="Symbol to use for the long leg")
    parser.add_argument("--short-symbol", required=True, help="Symbol to use for the short leg")
    parser.add_argument("--long-csv", required=True, help="CSV file containing long symbol bars")
    parser.add_argument("--short-csv", required=True, help="CSV file containing short symbol bars")
    parser.add_argument("--starting-cash", type=float, default=100000, help="Starting cash for the backtest")
    parser.add_argument("--lookback-bars", type=int, default=50, help="Lookback window for z-score calculation")
    parser.add_argument("--entry-zscore", type=float, default=2.0, help="Entry z-score threshold")
    parser.add_argument("--exit-zscore", type=float, default=0.5, help="Exit z-score threshold")
    parser.add_argument("--max-holding-bars", type=int, default=200, help="Maximum bars to hold a position")

    args = parser.parse_args()

    bars_by_symbol = load_bars_for_symbols_from_csv({
        args.long_symbol: args.long_csv,
        args.short_symbol: args.short_csv,
    })

    pair_config = PairConfig(
        name=f"{args.long_symbol}_{args.short_symbol}",
        symbol_long=args.long_symbol,
        symbol_short=args.short_symbol,
        lookback_bars=args.lookback_bars,
        entry_zscore=args.entry_zscore,
        exit_zscore=args.exit_zscore,
        max_holding_bars=args.max_holding_bars,
        notional_per_leg=args.starting_cash * 0.5,
    )

    risk_config = RiskConfig(
        max_total_notional=args.starting_cash,
        max_pairs_open=1,
        max_daily_loss=args.starting_cash * 0.2,
        max_position_per_symbol=args.starting_cash,
    )

    result = run_pairs_backtest(pair_config, risk_config, bars_by_symbol, args.starting_cash)

    starting_equity = float(_get_field(result, "starting_equity"))
    ending_equity = float(_get_field(result, "ending_equity"))
    total_return_pct = float(_get_field(result, "total_return_pct"))
    max_drawdown_pct = float(_get_field(result, "max_drawdown_pct"))
    trades = _get_field(result, "trades")
    trade_count = len(trades) if isinstance(trades, (list, tuple, set)) else int(trades)

    print(f"Starting equity: {starting_equity:.2f}")
    print(f"Ending equity: {ending_equity:.2f}")
    print(f"Total return: {total_return_pct:.2f}%")
    print(f"Max drawdown: {max_drawdown_pct:.2f}%")
    print(f"Number of trades: {trade_count}")


if __name__ == "__main__":
    main()
