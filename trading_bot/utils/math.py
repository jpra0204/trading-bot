"""Math helpers for rolling statistics and z-score calculations."""

from __future__ import annotations

def rolling_mean(values: list[float]) -> float:
    """Return the arithmetic mean of ``values``.

    Raises ``ValueError`` when ``values`` is empty to avoid silently returning
    misleading results.
    """

    if not values:
        raise ValueError("rolling_mean requires at least one value")
    return sum(values) / len(values)


def rolling_std(values: list[float]) -> float:
    """Return the population standard deviation of ``values``.

    Raises ``ValueError`` when ``values`` is empty. If variance is zero the
    function returns ``0.0`` to allow downstream callers to handle flat series
    gracefully.
    """

    if not values:
        raise ValueError("rolling_std requires at least one value")

    mean = rolling_mean(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return variance ** 0.5


def zscore(value: float, mean: float, std: float) -> float:
    """Compute the z-score of ``value`` given ``mean`` and ``std``.

    When ``std`` is zero (no variability), the function returns ``0.0`` to
    indicate a neutral z-score rather than raising.
    """

    if std == 0:
        return 0.0
    return (value - mean) / std

