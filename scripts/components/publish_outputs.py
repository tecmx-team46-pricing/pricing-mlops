#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scripts.run_azure_storage_flow import build_azure_credential
from scripts.upload_run_outputs import build_upload_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish Pricing MLOps component outputs to Azure Storage.")
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--storage-account", required=True)
    parser.add_argument("--run-artifacts-container", default="")
    parser.add_argument("--run-artifacts-prefix", default="")
    parser.add_argument("--environment", required=True)
    parser.add_argument("--run-owner", required=True)
    parser.add_argument("--compute-target", default="azure-ml")
    parser.add_argument("--trigger-type", default="manual")
    parser.add_argument("--curated-container", default="curated")
    parser.add_argument("--runs-container", default="runs")
    parser.add_argument("--snapshots-container", default="snapshots")
    parser.add_argument("--drift-logs-container", default="drift-logs")
    parser.add_argument("--reports-container", default="reports")
    parser.add_argument("--artifacts-container", default="artifacts")
    args = parser.parse_args()

    try:
        publish_component_outputs(
            run_dir=Path(args.run_dir) if args.run_dir else None,
            storage_account=args.storage_account,
            run_artifacts_container=args.run_artifacts_container,
            run_artifacts_prefix=args.run_artifacts_prefix,
            environment=args.environment,
            run_owner=args.run_owner,
            compute_target=args.compute_target,
            trigger_type=args.trigger_type,
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
    run_artifacts_container: str = "",
    run_artifacts_prefix: str = "",
) -> dict[str, str]:
    from azure.storage.blob import BlobServiceClient

    account_url = f"https://{storage_account}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url=account_url, credential=build_azure_credential())
    if run_dir is None:
        with tempfile.TemporaryDirectory(prefix="pricing-mlops-artifacts-") as tmpdir:
            return _download_and_publish(
                blob_service=blob_service,
                run_dir=Path(tmpdir),
                run_artifacts_container=run_artifacts_container,
                run_artifacts_prefix=run_artifacts_prefix,
                environment=environment,
                run_owner=run_owner,
                compute_target=compute_target,
                trigger_type=trigger_type,
                containers=containers,
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


def _download_and_publish(
    blob_service,
    run_dir: Path,
    run_artifacts_container: str,
    run_artifacts_prefix: str,
    environment: str,
    run_owner: str,
    compute_target: str,
    trigger_type: str,
    containers: dict[str, str],
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
        (run_dir / filename).write_bytes(blob.download_blob().readall())
    return _publish_from_dir(
        blob_service=blob_service,
        run_dir=run_dir,
        environment=environment,
        run_owner=run_owner,
        compute_target=compute_target,
        trigger_type=trigger_type,
        containers=containers,
    )


def _publish_from_dir(
    blob_service,
    run_dir: Path,
    environment: str,
    run_owner: str,
    compute_target: str,
    trigger_type: str,
    containers: dict[str, str],
) -> dict[str, str]:
    plan = build_upload_plan(
        run_dir=run_dir,
        environment=environment,
        run_owner=run_owner,
        compute_target=compute_target,
        trigger_type=trigger_type,
        containers=containers,
    )

    uploaded_blobs: dict[str, str] = {}
    for target in plan.values():
        print(
            "component publish: "
            f"container={target.container} "
            f"blob_path={target.blob_path} "
            f"source={target.source.name}"
        )
        blob = blob_service.get_blob_client(container=target.container, blob=target.blob_path)
        with target.source.open("rb") as handle:
            blob.upload_blob(handle, overwrite=True)
        uploaded_blobs[target.container] = target.blob_path
    return uploaded_blobs


if __name__ == "__main__":
    raise SystemExit(main())
