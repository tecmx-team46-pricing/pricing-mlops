from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping, Any


def evaluate_drift(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(records)
    metrics = [
        _numeric_metric(rows, "recommended_price", threshold_warning=0.25, threshold_critical=0.5),
        _numeric_metric(rows, "target_price", threshold_warning=0.25, threshold_critical=0.5),
    ]
    status = _overall_status(metrics)
    return {
        "status": status,
        "reason": "local template compares simple dispersion metrics from the current sample",
        "row_count": len(rows),
        "metrics": metrics,
        "recommended_action": _recommended_action(status),
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def _numeric_metric(
    rows: list[Mapping[str, Any]],
    variable: str,
    threshold_warning: float,
    threshold_critical: float,
) -> dict[str, Any]:
    values = [_to_float(row.get(variable)) for row in rows if row.get(variable) not in (None, "")]
    if not values:
        value = 0.0
    else:
        mean = sum(values) / len(values)
        value = 0.0 if mean == 0 else (max(values) - min(values)) / abs(mean)

    if value >= threshold_critical:
        status = "red"
    elif value >= threshold_warning:
        status = "yellow"
    else:
        status = "green"

    return {
        "variable": variable,
        "metric": "relative_range",
        "value": round(value, 6),
        "threshold_warning": threshold_warning,
        "threshold_critical": threshold_critical,
        "status": status,
    }


def _overall_status(metrics: list[Mapping[str, Any]]) -> str:
    statuses = {metric["status"] for metric in metrics}
    if "red" in statuses:
        return "red"
    if "yellow" in statuses:
        return "yellow"
    return "green"


def _recommended_action(status: str) -> str:
    if status == "red":
        return "block_and_review"
    if status == "yellow":
        return "review_before_promoting"
    return "continue"


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
