from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


KEY_COLUMNS = ("kpn", "vpareadescription", "distysegment")
PERCENTILE_COLUMNS = ("P20_PRICE", "P50_PRICE", "P85_PRICE")
OUTPUT_COLUMNS = (
    *KEY_COLUMNS,
    *PERCENTILE_COLUMNS,
    "n_transactions",
    "quantity_sum",
    "revenue_sum",
    "current_history_run_id",
    "history_snapshot_type",
)


@dataclass(frozen=True)
class CurrentAuthHistoryResult:
    output_path: Path
    row_count: int


def prepare_current_auth_history(
    input_path: str | Path,
    output_dir: str | Path,
    run_id: str,
) -> CurrentAuthHistoryResult:
    rows = _read_csv(Path(input_path))
    _require_columns(rows, [*KEY_COLUMNS, *PERCENTILE_COLUMNS])

    grouped: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in rows:
        key = tuple(str(row[column]) for column in KEY_COLUMNS)
        target = grouped.setdefault(
            key,
            {
                "kpn": key[0],
                "vpareadescription": key[1],
                "distysegment": key[2],
                "P20_PRICE": row.get("P20_PRICE", ""),
                "P50_PRICE": row.get("P50_PRICE", ""),
                "P85_PRICE": row.get("P85_PRICE", ""),
                "n_transactions": 0,
                "quantity_sum": 0.0,
                "revenue_sum": 0.0,
                "current_history_run_id": run_id,
                "history_snapshot_type": "current_auth_history_real",
            },
        )
        target["n_transactions"] = int(target["n_transactions"]) + 1
        target["quantity_sum"] = float(target["quantity_sum"]) + _to_float(
            row.get("quantity", row.get("quantity_sum"))
        )
        target["revenue_sum"] = float(target["revenue_sum"]) + _to_float(row.get("revenue_sum"))

    output_path = Path(output_dir) / "snapshots" / "current_auth_history_snapshot_real.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(output_path, list(grouped.values()))
    return CurrentAuthHistoryResult(output_path=output_path, row_count=len(grouped))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _require_columns(rows: list[dict[str, str]], required: list[str]) -> None:
    columns = set(rows[0]) if rows else set()
    missing = [column for column in required if column not in columns]
    if missing:
        raise ValueError(f"current AUTH history input is missing required columns: {missing}")


def _to_float(value: object) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(OUTPUT_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
