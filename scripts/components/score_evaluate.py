#!/usr/bin/env python
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from pricing_mlops.drift import evaluate_drift
from pricing_mlops.modeling.predict import score_pricing
from pricing_mlops.run import (
    LOGIC_VERSION,
    MODEL_VERSION,
    _render_report,
    git_commit_hash,
    read_csv_records,
    write_csv_records,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Score curated pricing data and write run artifacts.")
    parser.add_argument("--prepared-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--run-owner", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--input-blob-path", required=True)
    parser.add_argument("--trigger-type", default="manual")
    parser.add_argument("--model-repo", default="")
    parser.add_argument("--model-ref", default="")
    parser.add_argument("--model-commit-sha", default="")
    args = parser.parse_args()

    try:
        run_component(
            prepared_dir=Path(args.prepared_dir),
            output_dir=Path(args.output_dir),
            environment=args.environment,
            run_owner=args.run_owner,
            run_id=args.run_id,
            input_blob_path=args.input_blob_path,
            trigger_type=args.trigger_type,
            model_repo=args.model_repo,
            model_ref=args.model_ref,
            model_commit_sha=args.model_commit_sha,
        )
    except Exception as exc:
        print(f"score_evaluate failed: {exc}", file=sys.stderr)
        return 1
    return 0


def run_component(
    prepared_dir: Path,
    output_dir: Path,
    environment: str,
    run_owner: str,
    run_id: str,
    input_blob_path: str,
    trigger_type: str,
    model_repo: str = "",
    model_ref: str = "",
    model_commit_sha: str = "",
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    curated = read_csv_records(prepared_dir / "curated_input.csv")
    validation_metadata = json.loads((prepared_dir / "validation_metadata.json").read_text(encoding="utf-8"))

    started_at = datetime.now(timezone.utc)
    scored = score_pricing(curated)
    drift = evaluate_drift(scored)

    curated_path = output_dir / "curated_pricing.csv"
    snapshot_path = output_dir / "model_output_snapshot.csv"
    drift_path = output_dir / "model_drift_log.json"
    run_log_path = output_dir / "model_run_log.json"
    report_path = output_dir / "report.md"

    write_csv_records(curated_path, curated)
    write_csv_records(snapshot_path, scored)
    drift_path.write_text(json.dumps(drift, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    finished_at = datetime.now(timezone.utc)

    run_log = {
        "run_id": run_id,
        "status": "succeeded",
        "input_path": str(prepared_dir / "curated_input.csv"),
        "output_path": str(output_dir),
        "row_count": validation_metadata["row_count"],
        "validation_status": validation_metadata["validation_status"],
        "drift_status": drift["status"],
        "started_at_utc": started_at.isoformat(),
        "finished_at_utc": finished_at.isoformat(),
        "dataset_version": "local-sample",
        "schema_version": "pricing_input_schema_v1",
        "model_version": MODEL_VERSION,
        "logic_version": LOGIC_VERSION,
        "config_version": "pricing_rules_config_v1",
        "git_commit_hash": git_commit_hash(),
        "environment": environment,
        "owner": run_owner,
        "trigger_type": trigger_type,
        "input_blob_path": input_blob_path,
        "artifacts": {
            "curated_dataset": curated_path.name,
            "model_output_snapshot": snapshot_path.name,
            "model_drift_log": drift_path.name,
            "report": report_path.name,
        },
    }
    optional_metadata = {
        "model_repo": model_repo,
        "model_ref": model_ref,
        "model_commit_sha": model_commit_sha,
    }
    run_log.update({key: value for key, value in optional_metadata.items() if value})

    run_log_path.write_text(json.dumps(run_log, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(run_log, drift), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
