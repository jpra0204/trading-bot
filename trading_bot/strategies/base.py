"""Base interfaces for trading strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class Signal(Enum):
    """Discrete signals emitted by strategies."""

    ENTER_LONG_SHORT = "enter_long_short"
    ENTER_SHORT_LONG = "enter_short_long"
    EXIT = "exit"
    HOLD = "hold"


class Strategy(ABC):
    """Abstract strategy interface.

    The ``state`` parameter passed to each method can be a pair-specific state
    object (e.g., a ``PairState``) holding contextual information such as
    whether a position is open and how long it has been held.
    """

    @abstractmethod
    def generate_signal(self, state: Any) -> Signal:
        """Produce a trading signal from the current state."""

    @abstractmethod
    def execute(self, signal: Signal, state: Any) -> None:
        """Carry out broker actions for a given signal and update state."""

