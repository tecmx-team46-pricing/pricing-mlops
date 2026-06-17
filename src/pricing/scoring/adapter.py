from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


KEY_COLUMNS = ("kpn", "vpareadescription", "distysegment")
PERCENTILE_COLUMNS = ("P20_PRICE", "P50_PRICE", "P85_PRICE")
RECOMMENDATION_COLUMNS = (
    "Selected_Optimal_Price",
    "selected_recommended_price",
    "Balanced",
    "P50_PRICE",
    "current_price",
)


@dataclass(frozen=True)
class ScoringResult:
    output_path: Path
    row_count: int
    scoring_strategy: str
    recommendation_source_column: str


def score_recommendations(
    feature_table_path: str | Path,
    output_path: str | Path,
    run_id: str,
    scoring_strategy: str = "contract_passthrough_v1",
) -> ScoringResult:
    rows = _read_csv(Path(feature_table_path))
    columns = set(rows[0]) if rows else set()
    missing = [column for column in (*KEY_COLUMNS, *PERCENTILE_COLUMNS) if column not in columns]
    if missing:
        raise ValueError(f"scoring feature table is missing required columns: {missing}")
    recommendation_source_column = next((column for column in RECOMMENDATION_COLUMNS if column in columns), "")
    if not recommendation_source_column:
        raise ValueError(f"scoring feature table is missing recommendation source: {RECOMMENDATION_COLUMNS}")

    timestamp = datetime.now(UTC).isoformat()
    output_rows = [
        {
            **row,
            "Selected_Optimal_Price": row[recommendation_source_column],
            "recommendation_source_column": recommendation_source_column,
            "scoring_strategy": scoring_strategy,
            "model_output_version": "model_output_snapshot_v1",
            "scoring_run_id": run_id,
            "scored_at_utc": timestamp,
        }
        for row in rows
    ]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(output, output_rows)
    return ScoringResult(
        output_path=output,
        row_count=len(output_rows),
        scoring_strategy=scoring_strategy,
        recommendation_source_column=recommendation_source_column,
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
