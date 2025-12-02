"""Lightweight scheduler placeholder for controlling run cadence."""

from __future__ import annotations

from datetime import timedelta
from typing import Callable


class IntervalScheduler:
    """Calls a function at a fixed interval.

    This is intentionally minimal for the scaffold and can be replaced with a
    more feature-rich scheduler like APScheduler when needed.
    """

    def __init__(self, interval: timedelta) -> None:
        self.interval = interval

    def run(self, step: Callable[[], None]) -> None:
        # In a real implementation this would sleep and loop; here we simply
        # call the provided step once to illustrate usage.
        step()
