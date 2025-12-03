"""Mean-reversion pairs trading strategy implementation."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Tuple

from trading_bot.brokers.base import BrokerClient, BrokerError
from trading_bot.config.schemas import PairConfig, RiskConfig
from trading_bot.models.types import Bar, Position, Side
from trading_bot.strategies.base import Signal, Strategy
from trading_bot.utils import math


@dataclass
class PairState:
    """Lightweight container for pair-specific runtime state."""

    is_open: bool = False
    entry_zscore: float | None = None
    bars_held: int = 0
    last_zscore: float | None = None


class PairsMeanReversionStrategy(Strategy):
    """Simple z-score based mean-reversion strategy for a symbol pair."""

    def __init__(
        self,
        pair_config: PairConfig,
        risk_config: RiskConfig,
        broker: BrokerClient,
        logger: logging.Logger | None = None,
    ) -> None:
        self.pair_config = pair_config
        self.risk_config = risk_config
        self.broker = broker
        self.logger = logger or logging.getLogger(__name__)

    def _fetch_bars(self, symbol: str) -> list[Bar]:
        bars = self.broker.get_historical_bars(symbol, limit=self.pair_config.lookback_bars)
        if len(bars) < self.pair_config.lookback_bars:
            raise BrokerError(
                f"Not enough historical bars for {symbol}: expected {self.pair_config.lookback_bars}, got {len(bars)}"
            )
        return bars

    def compute_spread_and_zscore(self) -> Tuple[float, float]:
        """Compute the latest spread and corresponding z-score for the pair."""

        bars_long = self._fetch_bars(self.pair_config.symbol_long)
        bars_short = self._fetch_bars(self.pair_config.symbol_short)

        closes_long = [bar.close for bar in bars_long]
        closes_short = [bar.close for bar in bars_short]
        if len(closes_long) != len(closes_short):
            raise BrokerError("Historical series lengths for pair symbols do not match")

        spreads = [long - short for long, short in zip(closes_long, closes_short)]
        current_spread = spreads[-1]
        mean = math.rolling_mean(spreads)
        std = math.rolling_std(spreads)
        z_score = math.zscore(current_spread, mean, std)
        return current_spread, z_score

    def generate_signal(self, state: PairState) -> Signal:
        """Generate a trading signal based on the pair's spread z-score."""

        _spread, z_score = self.compute_spread_and_zscore()
        state.last_zscore = z_score

        if state.is_open:
            state.bars_held += 1
            if abs(z_score) < self.pair_config.exit_zscore or state.bars_held >= self.pair_config.max_holding_bars:
                return Signal.EXIT
            return Signal.HOLD

        if z_score > self.pair_config.entry_zscore:
            state.entry_zscore = z_score
            return Signal.ENTER_SHORT_LONG
        if z_score < -self.pair_config.entry_zscore:
            state.entry_zscore = z_score
            return Signal.ENTER_LONG_SHORT
        return Signal.HOLD

    def _position_quantity(self, symbol: str, notional: float) -> float:
        quote = self.broker.get_quote(symbol)
        if quote.last == 0:
            raise BrokerError(f"Cannot size position for {symbol} with zero price")
        return notional / quote.last

    def _close_position(self, position: Position) -> None:
        side: Side = "buy" if position.quantity < 0 else "sell"
        self.broker.place_order(position.symbol, side=side, quantity=abs(position.quantity))

    def execute(self, signal: Signal, state: PairState) -> None:
        """Execute broker actions for the provided signal and update state."""

        if signal == Signal.ENTER_LONG_SHORT:
            notional = self.pair_config.notional_per_leg
            qty_long = self._position_quantity(self.pair_config.symbol_long, notional)
            qty_short = self._position_quantity(self.pair_config.symbol_short, notional)
            self.broker.place_order(self.pair_config.symbol_long, side="buy", quantity=qty_long)
            self.broker.place_order(self.pair_config.symbol_short, side="sell", quantity=qty_short)
            state.is_open = True
            state.bars_held = 0
            return

        if signal == Signal.ENTER_SHORT_LONG:
            notional = self.pair_config.notional_per_leg
            qty_long = self._position_quantity(self.pair_config.symbol_long, notional)
            qty_short = self._position_quantity(self.pair_config.symbol_short, notional)
            self.broker.place_order(self.pair_config.symbol_long, side="sell", quantity=qty_long)
            self.broker.place_order(self.pair_config.symbol_short, side="buy", quantity=qty_short)
            state.is_open = True
            state.bars_held = 0
            return

        if signal == Signal.EXIT:
            pos_long = self.broker.get_position(self.pair_config.symbol_long)
            pos_short = self.broker.get_position(self.pair_config.symbol_short)
            if pos_long:
                self._close_position(pos_long)
            if pos_short:
                self._close_position(pos_short)
            state.is_open = False
            state.entry_zscore = None
            state.bars_held = 0
            return

        # HOLD: no action
        return

