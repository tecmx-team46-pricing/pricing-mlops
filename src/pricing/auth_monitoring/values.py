from __future__ import annotations


def to_float(value: object, default: float = float("nan")) -> float:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def is_nan(value: object) -> bool:
    return isinstance(value, float) and value != value

