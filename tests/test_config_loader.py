"""Tests for configuration loader and schemas."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from trading_bot.config.loader import load_run_config
from trading_bot.config.schemas import PairConfig, RunConfig


def test_loads_run_paper_example() -> None:
    config_path = Path("trading_bot/config/examples/run_paper_example.yaml")
    config = load_run_config(config_path)
    assert isinstance(config, RunConfig)
    assert config.mode == "paper"
    assert len(config.pairs) == 2
    assert config.risk.max_pairs_open == 2


def test_pair_config_validates_positive_thresholds() -> None:
    with pytest.raises(ValidationError):
        PairConfig(
            name="invalid",
            symbol_long="AAPL",
            symbol_short="MSFT",
            lookback_bars=0,
            entry_zscore=2.0,
            exit_zscore=0.5,
            max_holding_bars=10,
            notional_per_leg=1000,
        )
