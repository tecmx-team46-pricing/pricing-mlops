from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping, Any


def evaluate_drift(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(records)
    return {
        "status": "not_evaluated",
        "reason": "no baseline configured for local template flow",
        "row_count": len(rows),
        "metrics": [],
        "recommended_action": "collect_baseline",
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
