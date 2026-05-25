#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
import time

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scripts.run_azure_storage_flow import build_azure_credential
from scripts.components.score_evaluate import run_component as run_score_evaluate
from scripts.upload_run_outputs import publish_run_outputs_with_blob_sink
from pricing_mlops.artifact_publishing import ComponentStateLayout, PublishingConfig


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish Pricing MLOps component outputs to Azure Storage.")
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--score-token", default="")
    parser.add_argument("--storage-account", required=True)
    parser.add_argument("--run-artifacts-container", default="")
    parser.add_argument("--run-artifacts-prefix", default="")
    parser.add_argument("--environment", required=True)
    parser.add_argument("--run-owner", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--input-container", default="raw-masked")
    parser.add_argument("--input-blob-path", required=True)
    parser.add_argument("--compute-target", default="azure-ml")
    parser.add_argument("--trigger-type", default="manual")
    parser.add_argument("--model-repo", default="")
    parser.add_argument("--model-ref", default="")
    parser.add_argument("--model-commit-sha", default="")
    publishing_config = PublishingConfig.from_env()
    parser.add_argument("--curated-container", default=publishing_config.containers["curated"])
    parser.add_argument("--runs-container", default=publishing_config.containers["runs"])
    parser.add_argument("--snapshots-container", default=publishing_config.containers["snapshots"])
    parser.add_argument("--drift-logs-container", default=publishing_config.containers["drift_logs"])
    parser.add_argument("--reports-container", default=publishing_config.containers["reports"])
    parser.add_argument("--artifacts-container", default=publishing_config.containers["artifacts"])
    args = parser.parse_args()

    try:
        publish_component_outputs(
            run_dir=Path(args.run_dir) if args.run_dir else None,
            score_token=Path(args.score_token) if args.score_token else None,
            storage_account=args.storage_account,
            run_artifacts_container=args.run_artifacts_container,
            run_artifacts_prefix=args.run_artifacts_prefix,
            environment=args.environment,
            run_owner=args.run_owner,
            run_id=args.run_id,
            input_container=args.input_container,
            input_blob_path=args.input_blob_path,
            compute_target=args.compute_target,
            trigger_type=args.trigger_type,
            model_repo=args.model_repo,
            model_ref=args.model_ref,
            model_commit_sha=args.model_commit_sha,
            containers={
                "curated": args.curated_container,
                "runs": args.runs_container,
                "snapshots": args.snapshots_container,
                "drift_logs": args.drift_logs_container,
                "reports": args.reports_container,
                "artifacts": args.artifacts_container,
            },
        )
    except Exception as exc:
        print(f"publish_outputs failed: {exc}", file=sys.stderr)
        return 1
    return 0


def publish_component_outputs(
    run_dir: Path | None,
    storage_account: str,
    environment: str,
    run_owner: str,
    compute_target: str,
    trigger_type: str,
    containers: dict[str, str],
    score_token: Path | None = None,
    run_artifacts_container: str = "",
    run_artifacts_prefix: str = "",
    run_id: str = "",
    input_container: str = "raw-masked",
    input_blob_path: str = "",
    model_repo: str = "",
    model_ref: str = "",
    model_commit_sha: str = "",
) -> dict[str, str]:
    from azure.storage.blob import BlobServiceClient

    _require_flow_token(score_token, "score_evaluate")
    account_url = f"https://{storage_account}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url=account_url, credential=build_azure_credential())
    if run_dir is None:
        with tempfile.TemporaryDirectory(prefix="pricing-mlops-artifacts-") as tmpdir:
            return _download_and_publish(
                blob_service=blob_service,
                run_dir=Path(tmpdir),
                run_artifacts_container=run_artifacts_container,
                run_artifacts_prefix=run_artifacts_prefix,
                storage_account=storage_account,
                environment=environment,
                run_owner=run_owner,
                run_id=run_id,
                input_container=input_container,
                input_blob_path=input_blob_path,
                compute_target=compute_target,
                trigger_type=trigger_type,
                containers=containers,
                model_repo=model_repo,
                model_ref=model_ref,
                model_commit_sha=model_commit_sha,
            )
    return _publish_from_dir(
        blob_service=blob_service,
        run_dir=run_dir,
        environment=environment,
        run_owner=run_owner,
        compute_target=compute_target,
        trigger_type=trigger_type,
        containers=containers,
    )


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


def _download_and_publish(
    blob_service,
    run_dir: Path,
    run_artifacts_container: str,
    run_artifacts_prefix: str,
    storage_account: str,
    environment: str,
    run_owner: str,
    run_id: str,
    input_container: str,
    input_blob_path: str,
    compute_target: str,
    trigger_type: str,
    containers: dict[str, str],
    model_repo: str,
    model_ref: str,
    model_commit_sha: str,
) -> dict[str, str]:
    if not run_artifacts_container or not run_artifacts_prefix:
        raise ValueError("run artifacts container and prefix are required without --run-dir")
    run_dir.mkdir(parents=True, exist_ok=True)
    prefix = run_artifacts_prefix.strip("/")
    for filename in [
        "curated_pricing.csv",
        "model_output_snapshot.csv",
        "model_drift_log.json",
        "model_run_log.json",
        "report.md",
    ]:
        blob = blob_service.get_blob_client(container=run_artifacts_container, blob=f"{prefix}/{filename}")
        try:
            (run_dir / filename).write_bytes(_download_with_retry(blob, f"{prefix}/{filename}", attempts=6))
        except Exception as exc:
            print(f"run artifacts unavailable; rebuilding in publish_outputs: {exc}")
            run_score_evaluate(
                prepared_dir=None,
                output_dir=run_dir,
                environment=environment,
                run_owner=run_owner,
                run_id=run_id,
                input_blob_path=input_blob_path,
                trigger_type=trigger_type,
                storage_account=storage_account,
                input_container=input_container,
                prepared_container=run_artifacts_container,
                prepared_prefix=ComponentStateLayout().prepared_prefix(run_id),
                run_artifacts_container=run_artifacts_container,
                run_artifacts_prefix=run_artifacts_prefix,
                model_repo=model_repo,
                model_ref=model_ref,
                model_commit_sha=model_commit_sha,
            )
            break
    return _publish_from_dir(
        blob_service=blob_service,
        run_dir=run_dir,
        environment=environment,
        run_owner=run_owner,
        compute_target=compute_target,
        trigger_type=trigger_type,
        containers=containers,
    )


def _download_with_retry(blob, label: str, attempts: int = 60, delay_seconds: int = 10) -> bytes:
    for attempt in range(1, attempts + 1):
        try:
            return blob.download_blob().readall()
        except Exception as exc:
            if attempt == attempts:
                raise
            print(f"waiting for run artifact: {label} attempt={attempt} error={exc}")
            time.sleep(delay_seconds)
    raise RuntimeError(f"run artifact was not available: {label}")


def _publish_from_dir(
    blob_service,
    run_dir: Path,
    environment: str,
    run_owner: str,
    compute_target: str,
    trigger_type: str,
    containers: dict[str, str],
) -> dict[str, str]:
    result = publish_run_outputs_with_blob_sink(
        run_dir=run_dir,
        blob_service=blob_service,
        environment=environment,
        run_owner=run_owner,
        compute_target=compute_target,
        trigger_type=trigger_type,
        containers=containers,
    )
    if not result.ok:
        raise RuntimeError(f"component publish failed: {result}")
    return {
        uri.removeprefix("azureblob://").split("/", 1)[0]: uri.removeprefix("azureblob://").split("/", 1)[1]
        for uri in result.published.values()
    }


if __name__ == "__main__":
    raise SystemExit(main())
