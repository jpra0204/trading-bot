"""Minimal CLI entrypoint for running the trading bot."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from trading_bot.brokers.paper import PaperBrokerClient
from trading_bot.config.loader import load_run_config
from trading_bot.execution.runner import TradingRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the trading bot")
    parser.add_argument("--config", required=True, help="Path to a run configuration file")
    parser.add_argument("--mode", choices=["backtest", "paper", "live"], help="Override run mode")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    config_path = Path(args.config)
    config = load_run_config(config_path)
    if args.mode:
        config = config.model_copy(update={"mode": args.mode})

    if config.mode != "paper":
        raise NotImplementedError("Only paper mode is currently supported in the CLI")

    broker = PaperBrokerClient()
    runner = TradingRunner(config=config, broker=broker)
    runner.run_forever()


if __name__ == "__main__":
    main()
