"""Simple in-memory cache placeholder for data retrieval."""

from __future__ import annotations

from typing import Any, Mapping


class DataCache:
    """Minimal dictionary-backed cache for price data."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value

    def snapshot(self) -> Mapping[str, Any]:
        return dict(self._cache)
