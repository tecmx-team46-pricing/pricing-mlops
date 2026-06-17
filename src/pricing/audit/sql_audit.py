from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SqlAuditRecordSet:
    output_dir: Path
    table_counts: dict[str, int]


def build_sql_audit_records(
    *,
    run_id: str,
    status: str,
    baseline_version: str,
    model_output_version: str,
    artifact_manifest_path: str | Path,
    notification_payload_path: str | Path,
) -> dict[str, list[dict[str, Any]]]:
    manifest = _read_json(Path(artifact_manifest_path))
    notification_payload = _read_json(Path(notification_payload_path))
    timestamp = datetime.now(UTC).isoformat()

    return {
        "model_run_log": [
            {
                "run_id": run_id,
                "status": status,
                "baseline_version": baseline_version,
                "model_output_version": model_output_version,
                "created_at_utc": timestamp,
            }
        ],
        "snapshot_metadata": [
            {
                "run_id": run_id,
                "artifact_count": len(manifest.get("artifacts", [])),
                "manifest_schema_version": manifest.get("schema_version", ""),
                "created_at_utc": timestamp,
            }
        ],
        "operational_decisions": [
            {
                "run_id": run_id,
                "status": notification_payload.get("status", ""),
                "severity": notification_payload.get("severity", ""),
                "recommended_operational_action": notification_payload.get(
                    "recommended_operational_action", ""
                ),
                "should_notify": notification_payload.get("should_notify", False),
                "created_at_utc": timestamp,
            }
        ],
    }


def write_sql_audit_records(
    output_dir: str | Path,
    records: dict[str, list[dict[str, Any]]],
) -> SqlAuditRecordSet:
    target = Path(output_dir)
    table_counts: dict[str, int] = {}
    for table_name, table_rows in records.items():
        path = target / f"{table_name}.csv"
        _write_csv(path, table_rows)
        table_counts[table_name] = len(table_rows)
    return SqlAuditRecordSet(output_dir=target, table_counts=table_counts)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
