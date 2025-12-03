"""Execution runner tying together configuration, strategy, and broker."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict

from trading_bot.brokers.base import BrokerClient
from trading_bot.brokers.paper import PaperBrokerClient
from trading_bot.config.loader import load_run_config
from trading_bot.config.schemas import PairConfig, RunConfig
from trading_bot.strategies.pairs_mean_reversion import PairState, PairsMeanReversionStrategy
from trading_bot.strategies.base import Signal


class TradingRunner:
    """Run configured pairs strategies against a broker instance."""

    def __init__(self, config: RunConfig, broker: BrokerClient, logger: logging.Logger | None = None) -> None:
        self.config = config
        self.broker = broker
        self.logger = logger or logging.getLogger(__name__)
        self._strategies: Dict[str, PairsMeanReversionStrategy] = {}
        self._states: Dict[str, PairState] = {}

        for pair in self.config.pairs:
            self._strategies[pair.name] = PairsMeanReversionStrategy(pair, self.config.risk, broker, logger=self.logger)
            self._states[pair.name] = PairState()

    def _run_pair(self, pair_config: PairConfig) -> None:
        strategy = self._strategies[pair_config.name]
        state = self._states[pair_config.name]

        signal = strategy.generate_signal(state)
        self.logger.debug("Signal for %s: %s", pair_config.name, signal)

        strategy.execute(signal, state)
        if signal != Signal.HOLD:
            self.logger.info("Executed %s for %s", signal.value, pair_config.name)

    def run_once(self) -> None:
        """Run one evaluation/execute cycle across all configured pairs."""

        for pair in self.config.pairs:
            try:
                self._run_pair(pair)
            except Exception:
                self.logger.exception("Error while processing pair %s", pair.name)

    def run_forever(self) -> None:
        """Continuously run according to the configured polling interval."""

        while True:
            self.run_once()
            time.sleep(self.config.poll_interval_seconds)


def create_default_runner_from_file(config_path: str | Path, logger: logging.Logger | None = None) -> TradingRunner:
    """Load configuration and create a trading runner with a paper broker by default."""

    config = load_run_config(config_path)
    broker: BrokerClient = PaperBrokerClient()
    return TradingRunner(config=config, broker=broker, logger=logger)
