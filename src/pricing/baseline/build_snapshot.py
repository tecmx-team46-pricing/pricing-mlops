from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


BASELINE_VERSION = "baseline_mlops_pricing_v1"
OUTPUT_SCHEMA_VERSION = "model_output_snapshot_v1"
REQUIRED_COLUMNS = ("kpn", "vpareadescription", "distysegment", "P20_PRICE", "P50_PRICE", "P85_PRICE")
RECOMMENDATION_COLUMNS = (
    "Selected_Optimal_Price",
    "selected_recommended_price",
    "Balanced",
    "More_Profit",
    "Revenue_Aggressive",
)


@dataclass(frozen=True)
class BaselineSnapshotResult:
    output_path: Path
    row_count: int
    recommendation_column: str


def build_baseline_snapshot(
    feature_table_path: str | Path,
    output_path: str | Path,
    run_id: str,
) -> BaselineSnapshotResult:
    rows = _read_csv(Path(feature_table_path))
    columns = set(rows[0]) if rows else set()
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise ValueError(f"feature table is missing required baseline columns: {missing}")
    recommendation_column = next((column for column in RECOMMENDATION_COLUMNS if column in columns), "")
    if not recommendation_column:
        raise ValueError(f"feature table is missing recommendation column; tried {RECOMMENDATION_COLUMNS}")

    timestamp = datetime.now(UTC).isoformat()
    output_rows = [
        {
            **row,
            "run_id": run_id,
            "baseline_version": BASELINE_VERSION,
            "output_schema_version": OUTPUT_SCHEMA_VERSION,
            "run_timestamp_utc": timestamp,
            "recommendation_source_column": recommendation_column,
        }
        for row in rows
    ]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(output, output_rows)
    return BaselineSnapshotResult(
        output_path=output,
        row_count=len(output_rows),
        recommendation_column=recommendation_column,
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
