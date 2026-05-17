#!/usr/bin/env python
from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from pricing_mlops.run import run_local_flow
from scripts.upload_run_outputs import build_upload_plan


@dataclass(frozen=True)
class AzureStorageFlowRequest:
    storage_account: str
    environment: str
    run_owner: str
    run_id: str | None
    input_container: str
    input_blob_path: str
    containers: dict[str, str]


@dataclass(frozen=True)
class AzureStorageFlowResult:
    run_id: str
    row_count: int
    uploaded_blobs: dict[str, str]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Pricing MLOps flow inside Azure and write outputs to Azure Storage."
    )
    parser.add_argument("--storage-account", default=os.getenv("AZURE_STORAGE_ACCOUNT"))
    parser.add_argument("--environment", default=os.getenv("MLOPS_ENVIRONMENT", "staging"))
    parser.add_argument("--run-owner", default=os.getenv("MLOPS_RUN_OWNER", "team46"))
    parser.add_argument("--run-id", default=os.getenv("MLOPS_RUN_ID"))
    parser.add_argument(
        "--input-container",
        default=os.getenv("MLOPS_CONTAINER_RAW_MASKED", "raw-masked"),
    )
    parser.add_argument(
        "--input-blob-path",
        default=os.getenv("MLOPS_INPUT_BLOB_PATH", "samples/sample_pricing_v1.csv"),
    )
    parser.add_argument("--curated-container", default=os.getenv("MLOPS_CONTAINER_CURATED", "curated"))
    parser.add_argument("--runs-container", default=os.getenv("MLOPS_CONTAINER_RUNS", "runs"))
    parser.add_argument("--snapshots-container", default=os.getenv("MLOPS_CONTAINER_SNAPSHOTS", "snapshots"))
    parser.add_argument("--drift-logs-container", default=os.getenv("MLOPS_CONTAINER_DRIFT_LOGS", "drift-logs"))
    parser.add_argument("--reports-container", default=os.getenv("MLOPS_CONTAINER_REPORTS", "reports"))
    parser.add_argument("--artifacts-container", default=os.getenv("MLOPS_CONTAINER_ARTIFACTS", "artifacts"))
    args = parser.parse_args()

    if not args.storage_account:
        print("AZURE_STORAGE_ACCOUNT or --storage-account is required.", file=sys.stderr)
        return 4

    request = AzureStorageFlowRequest(
        storage_account=args.storage_account,
        environment=args.environment,
        run_owner=args.run_owner,
        run_id=args.run_id,
        input_container=args.input_container,
        input_blob_path=args.input_blob_path,
        containers={
            "curated": args.curated_container,
            "runs": args.runs_container,
            "snapshots": args.snapshots_container,
            "drift_logs": args.drift_logs_container,
            "reports": args.reports_container,
            "artifacts": args.artifacts_container,
        },
    )
    try:
        result = run_azure_storage_flow(request)
    except Exception as exc:
        print(f"azure flow failed: {exc}", file=sys.stderr)
        return 1

    print(f"azure flow succeeded: run_id={result.run_id}")
    return 0


def run_azure_storage_flow(request: AzureStorageFlowRequest) -> AzureStorageFlowResult:
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient
    except ImportError as exc:
        raise RuntimeError(f"Azure SDK dependency is missing: {exc}") from exc

    account_url = f"https://{request.storage_account}.blob.core.windows.net"
    credential = DefaultAzureCredential()
    blob_service = BlobServiceClient(account_url=account_url, credential=credential)

    print(
        "azure flow input: "
        f"storage_account={request.storage_account} "
        f"container={request.input_container} "
        f"blob_path={request.input_blob_path}"
    )

    with tempfile.TemporaryDirectory(prefix="pricing-mlops-") as tmpdir:
        tmp_path = Path(tmpdir)
        input_path = tmp_path / "input.csv"
        output_root = tmp_path / "runs"

        input_blob = blob_service.get_blob_client(
            container=request.input_container,
            blob=request.input_blob_path,
        )
        input_path.write_bytes(input_blob.download_blob().readall())

        result = run_local_flow(
            input_path=input_path,
            output_root=output_root,
            run_id=request.run_id,
        )
        print(f"azure flow run: run_id={result.run_id} run_dir={result.run_dir}")

        plan = build_upload_plan(
            run_dir=result.run_dir,
            environment=request.environment,
            run_owner=request.run_owner,
            containers=request.containers,
        )

        uploaded_blobs: dict[str, str] = {}
        for target in plan.values():
            print(
                "azure flow upload plan: "
                f"container={target.container} "
                f"blob_path={target.blob_path} "
                f"source={target.source.name}"
            )
            output_blob = blob_service.get_blob_client(
                container=target.container,
                blob=target.blob_path,
            )
            with target.source.open("rb") as handle:
                output_blob.upload_blob(handle, overwrite=True)
            uploaded_blobs[target.container] = target.blob_path

    return AzureStorageFlowResult(
        run_id=result.run_id,
        row_count=result.row_count,
        uploaded_blobs=uploaded_blobs,
    )


if __name__ == "__main__":
    raise SystemExit(main())
