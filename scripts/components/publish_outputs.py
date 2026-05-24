#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scripts.run_azure_storage_flow import build_azure_credential
from scripts.upload_run_outputs import build_upload_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish Pricing MLOps component outputs to Azure Storage.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--storage-account", required=True)
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
            run_dir=Path(args.run_dir),
            storage_account=args.storage_account,
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
    run_dir: Path,
    storage_account: str,
    environment: str,
    run_owner: str,
    compute_target: str,
    trigger_type: str,
    containers: dict[str, str],
) -> dict[str, str]:
    from azure.storage.blob import BlobServiceClient

    account_url = f"https://{storage_account}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url=account_url, credential=build_azure_credential())
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
