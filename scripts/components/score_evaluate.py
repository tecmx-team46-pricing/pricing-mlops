#!/usr/bin/env python
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

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
    parser.add_argument("--prepared-dir", default="")
    parser.add_argument("--validation-token", default="")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--flow-token", default="")
    parser.add_argument("--storage-account", default="")
    parser.add_argument("--prepared-container", default="")
    parser.add_argument("--prepared-prefix", default="")
    parser.add_argument("--run-artifacts-container", default="")
    parser.add_argument("--run-artifacts-prefix", default="")
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
            prepared_dir=Path(args.prepared_dir) if args.prepared_dir else None,
            validation_token=Path(args.validation_token) if args.validation_token else None,
            output_dir=Path(args.output_dir),
            flow_token=Path(args.flow_token) if args.flow_token else None,
            storage_account=args.storage_account,
            prepared_container=args.prepared_container,
            prepared_prefix=args.prepared_prefix,
            run_artifacts_container=args.run_artifacts_container,
            run_artifacts_prefix=args.run_artifacts_prefix,
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
    prepared_dir: Path | None,
    output_dir: Path,
    environment: str,
    run_owner: str,
    run_id: str,
    input_blob_path: str,
    trigger_type: str,
    validation_token: Path | None = None,
    flow_token: Path | None = None,
    storage_account: str = "",
    prepared_container: str = "",
    prepared_prefix: str = "",
    run_artifacts_container: str = "",
    run_artifacts_prefix: str = "",
    model_repo: str = "",
    model_ref: str = "",
    model_commit_sha: str = "",
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _require_flow_token(validation_token, "validate_prepare")
    if prepared_dir is None:
        prepared_dir = output_dir / "_prepared"
        _download_prefix(
            storage_account=storage_account,
            container=prepared_container,
            blob_prefix=prepared_prefix,
            destination=prepared_dir,
            filenames=["curated_input.csv", "validation_metadata.json"],
        )
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
    if storage_account and run_artifacts_container and run_artifacts_prefix:
        _upload_files(
            storage_account=storage_account,
            container=run_artifacts_container,
            blob_prefix=run_artifacts_prefix,
            files=[curated_path, snapshot_path, drift_path, run_log_path, report_path],
        )
    _write_flow_token(flow_token, {"stage": "score_evaluate", "run_id": run_id})


def _blob_service(storage_account: str):
    from azure.storage.blob import BlobServiceClient

    from scripts.run_azure_storage_flow import build_azure_credential

    account_url = f"https://{storage_account}.blob.core.windows.net"
    return BlobServiceClient(account_url=account_url, credential=build_azure_credential())


def _download_prefix(
    storage_account: str,
    container: str,
    blob_prefix: str,
    destination: Path,
    filenames: list[str],
) -> None:
    if not storage_account or not container or not blob_prefix:
        raise ValueError("storage account, prepared container and prepared prefix are required without --prepared-dir")
    destination.mkdir(parents=True, exist_ok=True)
    blob_service = _blob_service(storage_account)
    prefix = blob_prefix.strip("/")
    for filename in filenames:
        blob = blob_service.get_blob_client(container=container, blob=f"{prefix}/{filename}")
        (destination / filename).write_bytes(_download_with_retry(blob, f"{prefix}/{filename}"))


def _download_with_retry(blob, label: str, attempts: int = 60, delay_seconds: int = 10) -> bytes:
    for attempt in range(1, attempts + 1):
        try:
            return blob.download_blob().readall()
        except Exception as exc:
            if attempt == attempts:
                raise
            print(f"waiting for prepared artifact: {label} attempt={attempt} error={exc}")
            time.sleep(delay_seconds)
    raise RuntimeError(f"prepared artifact was not available: {label}")


def _upload_files(storage_account: str, container: str, blob_prefix: str, files: list[Path]) -> None:
    blob_service = _blob_service(storage_account)
    prefix = blob_prefix.strip("/")
    for file_path in files:
        blob = blob_service.get_blob_client(container=container, blob=f"{prefix}/{file_path.name}")
        with file_path.open("rb") as handle:
            blob.upload_blob(handle, overwrite=True)


def _require_flow_token(flow_token: Path | None, expected_stage: str) -> None:
    if flow_token is None:
        return
    if flow_token.suffix != ".json":
        flow_token = flow_token / "flow_token.json"
    if not flow_token.exists():
        raise FileNotFoundError(f"flow token is missing: {flow_token}")
    token = json.loads(flow_token.read_text(encoding="utf-8"))
    if token.get("stage") != expected_stage:
        raise ValueError(f"flow token expected stage {expected_stage}, got {token.get('stage')}")


def _write_flow_token(flow_token: Path | None, payload: dict[str, str]) -> None:
    if flow_token is None:
        return
    if flow_token.suffix != ".json":
        flow_token = flow_token / "flow_token.json"
    flow_token.parent.mkdir(parents=True, exist_ok=True)
    flow_token.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
