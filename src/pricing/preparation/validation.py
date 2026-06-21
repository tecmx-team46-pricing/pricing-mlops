from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


KEY_COLUMNS = ("kpn", "vpareadescription", "distysegment")
PRICE_COLUMNS = ("current_price", "rslpriceusd")
TRANSACTIONAL_COLUMNS = ("date", "dateperiod", "invoicenumber", "quantity")
PERCENTILE_COLUMNS = ("P0_PRICE", "P20_PRICE", "P50_PRICE", "P85_PRICE", "P100_PRICE")


@dataclass(frozen=True)
class ValidationResult:
    status: str
    row_count: int
    columns: list[str]


def validate_pricing_input(records: Iterable[Mapping[str, Any]]) -> ValidationResult:
    rows = [dict(record) for record in records]
    if not rows:
        raise ValueError("dataset is empty")

    columns = list(rows[0].keys())
    missing = [column for column in KEY_COLUMNS if column not in columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")
    if not any(column in columns for column in PRICE_COLUMNS):
        raise ValueError("missing required price column: current_price or rslpriceusd")

    if all(column in columns for column in PERCENTILE_COLUMNS):
        for index, row in enumerate(rows, start=1):
            values = [_to_float(row[column], column, index) for column in PERCENTILE_COLUMNS]
            if values != sorted(values):
                raise ValueError(
                    "percentile prices must be monotonic for row "
                    f"{index}: {', '.join(PERCENTILE_COLUMNS)}"
                )

    if all(column in columns for column in KEY_COLUMNS) and not _is_transactional_input(columns):
        seen: set[tuple[str, str, str]] = set()
        for row in rows:
            key = tuple(str(row[column]) for column in KEY_COLUMNS)
            if key in seen:
                raise ValueError(
                    "duplicate pricing keys found for "
                    "[kpn, vpareadescription, distysegment]"
                )
            seen.add(key)

    return ValidationResult(status="passed", row_count=len(rows), columns=columns)


def _is_transactional_input(columns: list[str]) -> bool:
    return any(column in columns for column in TRANSACTIONAL_COLUMNS)


def _to_float(value: Any, column: str, row_index: int) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"column {column} must be numeric in row {row_index}") from exc
