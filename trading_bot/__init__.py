"""Top-level package for the configuration-driven trading bot.

This package exposes reusable components for strategies, brokers, and
execution utilities. Modules are organized to keep domain concerns
well separated and easy to extend.
"""

__all__ = [
    "config",
    "brokers",
    "data",
    "strategies",
    "execution",
    "portfolio",
    "models",
    "utils",
]
