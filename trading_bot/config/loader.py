"""Utilities for loading trading bot configuration files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from pydantic import ValidationError

from trading_bot.config.schemas import RunConfig


def _load_yaml(path: Path) -> Mapping[str, Any]:
    """Load YAML content from disk using PyYAML."""

    try:
        import yaml
    except ModuleNotFoundError as exc:  # pragma: no cover - import guard
        raise ModuleNotFoundError("PyYAML is required to load YAML configs. Install pyyaml>=6.0.") from exc
    return yaml.safe_load(path.read_text())


def _load_raw(path: Path) -> Mapping[str, Any]:
    """Load a JSON or YAML config into a raw mapping."""

    if path.suffix.lower() in {".yaml", ".yml"}:
        return _load_yaml(path)
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text())
    raise ValueError("Unsupported config format. Use YAML or JSON.")


def load_run_config(path: Path | str) -> RunConfig:
    """Load a :class:`RunConfig` from a JSON or YAML file."""

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    raw = _load_raw(config_path)
    if not isinstance(raw, Mapping):
        raise ValueError("Config file must parse to a mapping/dictionary")

    try:
        return RunConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError("Invalid configuration data") from exc


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    example_path = Path(__file__).resolve().parent / "examples" / "run_paper_example.yaml"
    print(load_run_config(example_path))
