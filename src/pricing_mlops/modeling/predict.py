from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping, Any


def score_pricing(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    timestamp = datetime.now(timezone.utc).isoformat()
    scored: list[dict[str, Any]] = []

    for record in records:
        row = dict(record)
        current_price = _to_float(row.get("current_price"), default=0.0)
        recommended_price = _recommended_price(row, current_price)
        delta = recommended_price - current_price

        row["recommended_price"] = round(recommended_price, 4)
        row["pricing_action"] = _pricing_action(delta, current_price)
        row["score_timestamp_utc"] = timestamp
        scored.append(row)

    return scored


def _recommended_price(row: Mapping[str, Any], current_price: float) -> float:
    if row.get("P50_PRICE") not in (None, ""):
        return _to_float(row["P50_PRICE"], default=current_price)
    return current_price


def _pricing_action(delta: float, current_price: float) -> str:
    if current_price == 0:
        return "hold"

    ratio = delta / current_price
    if ratio > 0.01:
        return "review_increase"
    if ratio < -0.01:
        return "review_decrease"
    return "hold"


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
