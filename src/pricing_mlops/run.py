from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from uuid import uuid4

from pricing_mlops.drift import evaluate_drift
from pricing_mlops.modeling.predict import score_pricing
from pricing_mlops.validation import validate_pricing_input


@dataclass(frozen=True)
class LocalFlowResult:
    run_id: str
    run_dir: Path
    row_count: int


def run_local_flow(
    input_path: str | Path,
    output_root: str | Path,
    run_id: str | None = None,
) -> LocalFlowResult:
    started_at = datetime.now(timezone.utc)
    source_path = Path(input_path)
    output_base = Path(output_root)
    rows = read_csv_records(source_path)
    validation = validate_pricing_input(rows)
    curated = curate_pricing_records(rows)
    scored = score_pricing(curated)
    drift = evaluate_drift(scored)

    run_id = run_id or generate_run_id()
    run_dir = output_base / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    curated_path = run_dir / "curated_pricing.csv"
    snapshot_path = run_dir / "model_output_snapshot.csv"
    drift_path = run_dir / "model_drift_log.json"
    run_log_path = run_dir / "model_run_log.json"
    report_path = run_dir / "report.md"

    write_csv_records(curated_path, curated)
    write_csv_records(snapshot_path, scored)
    drift_path.write_text(json.dumps(drift, indent=2, sort_keys=True) + "\n")
    finished_at = datetime.now(timezone.utc)

    run_log = {
        "run_id": run_id,
        "status": "succeeded",
        "input_path": str(source_path),
        "output_path": str(run_dir),
        "row_count": validation.row_count,
        "validation_status": validation.status,
        "drift_status": drift["status"],
        "started_at_utc": started_at.isoformat(),
        "finished_at_utc": finished_at.isoformat(),
        "dataset_version": "local-sample",
        "schema_version": "pricing_input_schema_v1",
        "model_version": "pricing-pass-through-template/0.1.0",
        "config_version": "pricing_rules_config_v1",
        "git_commit_hash": git_commit_hash(),
        "artifacts": {
            "curated_dataset": curated_path.name,
            "model_output_snapshot": snapshot_path.name,
            "model_drift_log": drift_path.name,
            "report": report_path.name,
        },
    }
    run_log_path.write_text(json.dumps(run_log, indent=2, sort_keys=True) + "\n")
    report_path.write_text(_render_report(run_log, drift))

    return LocalFlowResult(run_id=run_id, run_dir=run_dir, row_count=validation.row_count)


def generate_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid4().hex[:8]}"


def read_csv_records(path: str | Path) -> list[dict[str, str]]:
    csv_path = Path(path)
    with csv_path.open(newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def curate_pricing_records(records: list[dict[str, str]]) -> list[dict[str, object]]:
    numeric_columns = (
        "current_price",
        "rslpriceusd",
        "quantity",
        "P0_PRICE",
        "P20_PRICE",
        "P50_PRICE",
        "P85_PRICE",
        "P100_PRICE",
    )
    curated: list[dict[str, object]] = []
    for record in records:
        row: dict[str, object] = {}
        for key, value in record.items():
            normalized_key = key.strip()
            if normalized_key in numeric_columns:
                row[normalized_key] = _to_float(value)
            else:
                row[normalized_key] = value.strip() if isinstance(value, str) else value
        if "current_price" not in row and "rslpriceusd" in row:
            row["current_price"] = row["rslpriceusd"]
        curated.append(row)
    return curated


def write_csv_records(path: str | Path, records: list[dict[str, object]]) -> None:
    output_path = Path(path)
    if not records:
        output_path.write_text("")
        return

    fieldnames = list(records[0].keys())
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def _render_report(run_log: dict[str, object], drift: dict[str, object]) -> str:
    return "\n".join(
        [
            "# Pricing MLOps Local Run Report",
            "",
            f"- Run ID: `{run_log['run_id']}`",
            f"- Status: `{run_log['status']}`",
            f"- Rows processed: `{run_log['row_count']}`",
            f"- Validation: `{run_log['validation_status']}`",
            f"- Drift: `{drift['status']}`",
            f"- Decision: `{_decision_for_status(str(drift['status']))}`",
            f"- Snapshot generated: `{run_log['artifacts']['model_output_snapshot']}`",
            f"- Recommended action: `{drift['recommended_action']}`",
            "",
            "This report is generated from synthetic or masked inputs only.",
            "",
        ]
    )


def git_commit_hash() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip()


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _decision_for_status(status: str) -> str:
    if status == "red":
        return "red - block and review"
    if status == "yellow":
        return "yellow - review before promoting"
    return "green - continue"
