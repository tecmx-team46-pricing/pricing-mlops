import csv
import json

from pricing.audit import build_sql_audit_records, write_sql_audit_records


def test_sql_audit_writer_materializes_auditable_table_rows(tmp_path):
    manifest = tmp_path / "artifact_manifest.json"
    payload = tmp_path / "notification_payload.json"
    output_dir = tmp_path / "audit"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "artifact_manifest_v1",
                "artifacts": [{"relative_path": "summaries/notification_payload.json"}],
            }
        ),
        encoding="utf-8",
    )
    payload.write_text(
        json.dumps(
            {
                "status": "Yellow",
                "severity": "warning",
                "recommended_operational_action": "REVIEW",
                "should_notify": True,
            }
        ),
        encoding="utf-8",
    )

    records = build_sql_audit_records(
        run_id="run-1",
        status="completed",
        baseline_version="baseline-v1",
        model_output_version="model-output-v1",
        artifact_manifest_path=manifest,
        notification_payload_path=payload,
    )
    result = write_sql_audit_records(output_dir, records)

    assert result.table_counts == {
        "model_run_log": 1,
        "snapshot_metadata": 1,
        "operational_decisions": 1,
    }
    with (output_dir / "operational_decisions.csv").open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["run_id"] == "run-1"
    assert row["status"] == "Yellow"
    assert row["recommended_operational_action"] == "REVIEW"
