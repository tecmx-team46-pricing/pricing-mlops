from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping, Any


def score_pricing(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    timestamp = datetime.now(timezone.utc).isoformat()
    scored: list[dict[str, Any]] = []

    for record in records:
        row = dict(record)
        current_price = _to_float(row.get("current_price"), default=0.0)
        recommended_price = _rule_price(row, "P50_PRICE", current_price)
        floor_price = _rule_price(row, "P20_PRICE", recommended_price)
        target_price = _rule_price(row, "P85_PRICE", recommended_price)
        delta = recommended_price - current_price

        row["floor_price"] = round(floor_price, 4)
        row["recommended_price"] = round(recommended_price, 4)
        row["target_price"] = round(target_price, 4)
        row["pricing_action"] = _pricing_action(delta, current_price)
        row["score_timestamp_utc"] = timestamp
        scored.append(row)

    return scored


def _rule_price(row: Mapping[str, Any], column: str, default: float) -> float:
    if row.get(column) not in (None, ""):
        return _to_float(row[column], default=default)
    return default


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
