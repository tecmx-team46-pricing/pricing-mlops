#!/usr/bin/env python
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from pricing_mlops.artifacts import ArtifactLayout, AzureBlobArtifactSink, PublishingConfig, RunPartition
from pricing_mlops.run import run_local_flow


@dataclass(frozen=True)
class AzureStorageFlowRequest:
    storage_account: str
    environment: str
    run_owner: str
    compute_target: str | None
    trigger_type: str | None
    model_repo: str | None
    model_ref: str | None
    model_commit_sha: str | None
    run_id: str | None
    output_root: str | None
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
    parser.add_argument("--compute-target", default=os.getenv("MLOPS_COMPUTE_TARGET"))
    parser.add_argument("--trigger-type", default=os.getenv("MLOPS_TRIGGER_TYPE"))
    parser.add_argument("--model-repo", default=os.getenv("MODEL_REPO_GITHUB"))
    parser.add_argument("--model-ref", default=os.getenv("MODEL_REPO_REF"))
    parser.add_argument("--model-commit-sha", default=os.getenv("MODEL_REPO_COMMIT_SHA"))
    parser.add_argument("--run-id", default=os.getenv("MLOPS_RUN_ID"))
    parser.add_argument("--output-root", default=os.getenv("MLOPS_OUTPUT_ROOT"))
    parser.add_argument(
        "--input-container",
        default=os.getenv("MLOPS_CONTAINER_RAW_MASKED", "raw-masked"),
    )
    parser.add_argument(
        "--input-blob-path",
        default=os.getenv(
            "MLOPS_INPUT_BLOB_PATH",
            os.getenv("INPUT_BLOB_PATH", "samples/sample_pricing_v1.csv"),
        ),
    )
    publishing_config = PublishingConfig.from_env()
    parser.add_argument("--curated-container", default=publishing_config.containers["curated"])
    parser.add_argument("--runs-container", default=publishing_config.containers["runs"])
    parser.add_argument("--snapshots-container", default=publishing_config.containers["snapshots"])
    parser.add_argument("--drift-logs-container", default=publishing_config.containers["drift_logs"])
    parser.add_argument("--reports-container", default=publishing_config.containers["reports"])
    parser.add_argument("--artifacts-container", default=publishing_config.containers["artifacts"])
    args = parser.parse_args()

    if not args.storage_account:
        print("AZURE_STORAGE_ACCOUNT or --storage-account is required.", file=sys.stderr)
        return 4

    request = AzureStorageFlowRequest(
        storage_account=args.storage_account,
        environment=args.environment,
        run_owner=args.run_owner,
        compute_target=args.compute_target,
        trigger_type=args.trigger_type,
        model_repo=args.model_repo,
        model_ref=args.model_ref,
        model_commit_sha=args.model_commit_sha,
        run_id=resolve_run_id(args.run_id),
        output_root=args.output_root,
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
        from azure.storage.blob import BlobServiceClient
    except ImportError as exc:
        raise RuntimeError(f"Azure SDK dependency is missing: {exc}") from exc

    account_url = f"https://{request.storage_account}.blob.core.windows.net"
    credential = build_azure_credential()
    blob_service = BlobServiceClient(account_url=account_url, credential=credential)

    print(
        "azure flow input: "
        f"storage_account={request.storage_account} "
        f"container={request.input_container} "
        f"blob_path={request.input_blob_path}"
    )

    if request.output_root:
        output_root = Path(request.output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="pricing-mlops-input-") as tmpdir:
            result, uploaded_blobs = _run_and_upload(request, blob_service, Path(tmpdir), output_root)
    else:
        with tempfile.TemporaryDirectory(prefix="pricing-mlops-") as tmpdir:
            tmp_path = Path(tmpdir)
            result, uploaded_blobs = _run_and_upload(request, blob_service, tmp_path, tmp_path / "runs")

    return AzureStorageFlowResult(
        run_id=result.run_id,
        row_count=result.row_count,
        uploaded_blobs=uploaded_blobs,
    )


def build_azure_credential():
    if os.getenv("AZUREML_RUN_ID") and os.getenv("MLOPS_FORCE_DEFAULT_CREDENTIAL", "false").lower() != "true":
        try:
            from azure.ai.ml.identity import AzureMLOnBehalfOfCredential

            return AzureMLOnBehalfOfCredential()
        except ImportError:
            pass

    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()


def resolve_run_id(run_id: str | None) -> str | None:
    if os.getenv("AZUREML_RUN_ID") and (not run_id or run_id == "manual"):
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-azure-ml")
    return run_id


def _run_and_upload(
    request: AzureStorageFlowRequest,
    blob_service,
    tmp_path: Path,
    output_root: Path,
):
    input_path = tmp_path / "input.csv"
    input_blob = blob_service.get_blob_client(
        container=request.input_container,
        blob=request.input_blob_path,
    )
    input_path.write_bytes(input_blob.download_blob().readall())

    result = run_local_flow(
        input_path=input_path,
        output_root=output_root,
        run_id=request.run_id,
        run_metadata=_run_metadata(request),
    )
    print(f"azure flow run: run_id={result.run_id} run_dir={result.run_dir}")

    if result.run_result is None:
        raise RuntimeError("run_local_flow did not return a neutral RunResult")
    publish_result = AzureBlobArtifactSink(
        blob_service=blob_service,
        layout=ArtifactLayout.default(request.containers),
        partition=RunPartition(
            environment=request.environment,
            owner=request.run_owner,
            compute_target=request.compute_target,
            trigger_type=request.trigger_type,
            run_id=result.run_id,
        ),
    ).publish(result.run_result)
    if not publish_result.ok:
        raise RuntimeError(f"Azure Blob publish failed: {publish_result}")
    uploaded_blobs = {
        published_uri.removeprefix("azureblob://").split("/", 1)[0]: published_uri.removeprefix("azureblob://").split("/", 1)[1]
        for sink in publish_result.sinks
        for published_uri in sink.published.values()
        if published_uri.startswith("azureblob://")
    }
    return result, uploaded_blobs


def _run_metadata(request: AzureStorageFlowRequest) -> dict[str, str]:
    metadata = {
        "environment": request.environment,
        "owner": request.run_owner,
        "trigger_type": request.trigger_type or "manual",
        "input_blob_path": request.input_blob_path,
    }
    optional_values = {
        "model_repo": request.model_repo,
        "model_ref": request.model_ref,
        "model_commit_sha": request.model_commit_sha,
    }
    metadata.update({key: value for key, value in optional_values.items() if value})
    return metadata


if __name__ == "__main__":
    raise SystemExit(main())
