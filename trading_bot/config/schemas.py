"""Pydantic configuration schemas for the trading bot."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PairConfig(BaseModel):
    """Configuration for a single tradeable equity pair."""

    model_config = ConfigDict(frozen=True)

    name: str
    symbol_long: str
    symbol_short: str
    lookback_bars: int
    entry_zscore: float
    exit_zscore: float
    max_holding_bars: int
    notional_per_leg: float

    @field_validator("lookback_bars", "max_holding_bars")
    @classmethod
    def _validate_positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("lookback and holding periods must be positive")
        return value

    @field_validator("entry_zscore", "exit_zscore")
    @classmethod
    def _validate_positive_zscore(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("z-score thresholds must be greater than zero")
        return value

    @field_validator("notional_per_leg")
    @classmethod
    def _validate_positive_notional(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("notional per leg must be positive")
        return value


class RiskConfig(BaseModel):
    """Global risk limits applied across pairs and sessions."""

    model_config = ConfigDict(frozen=True)

    max_total_notional: float
    max_pairs_open: int
    max_daily_loss: float
    max_position_per_symbol: float

    @field_validator("max_total_notional", "max_daily_loss", "max_position_per_symbol")
    @classmethod
    def _validate_positive_float(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("risk limits must be positive values")
        return value

    @field_validator("max_pairs_open")
    @classmethod
    def _validate_positive_pairs(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("max_pairs_open must be positive")
        return value


class RunConfig(BaseModel):
    """Top-level configuration used by backtest and live runners."""

    model_config = ConfigDict(frozen=True)

    mode: Literal["backtest", "paper", "live"]
    poll_interval_seconds: int = Field(..., description="Polling cadence for price updates")
    pairs: list[PairConfig]
    risk: RiskConfig

    @field_validator("poll_interval_seconds")
    @classmethod
    def _validate_positive_poll_interval(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("poll_interval_seconds must be positive")
        return value
