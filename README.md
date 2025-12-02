# Trading Bot

Reusable, configuration-driven pairs trading bot scaffold. This project separates configuration, strategy logic, broker integration, and execution so strategies can be swapped or extended with minimal code changes.

## Layout
- `trading_bot/`: Package source
  - `config/`: Configuration schemas and loader utilities
  - `brokers/`: Broker client interfaces and implementations
  - `data/`: Data source abstractions for historical or live feeds
  - `strategies/`: Strategy interfaces and concrete strategies
  - `execution/`: Execution loop and scheduling utilities
  - `portfolio/`: Risk and accounting helpers
  - `models/`: Shared domain models
  - `utils/`: Shared helpers
- `tests/`: Pytest suite for key components

## Getting Started
1. Install dependencies: `python -m pip install -e .[dev]`
2. Load a sample configuration from `trading_bot/config/examples/pairs_mean_reversion.json`.
3. Extend brokers or strategies as needed for your environment.
