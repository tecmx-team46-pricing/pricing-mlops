#!/usr/bin/env python
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Callable

from pricing_mlops.artifact_publishing import ArtifactLayout, AzureBlobArtifactSink, PublishingConfig, RunMetadata, RunPartition, RunResult
from pricing_mlops.artifact_publishing.layout import manifest_from_run_dir


@dataclass(frozen=True)
class UploadTarget:
    source: Path
    container: str
    blob_path: str


Runner = Callable[[list[str]], object]


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload Pricing MLOps run outputs to Azure Storage.")
    parser.add_argument("--run-dir", required=True, help="Local run output directory.")
    parser.add_argument("--storage-account", default=os.getenv("AZURE_STORAGE_ACCOUNT"))
    parser.add_argument("--environment", default=os.getenv("MLOPS_ENVIRONMENT", "staging"))
    parser.add_argument("--run-owner", default=os.getenv("MLOPS_RUN_OWNER", "team46"))
    parser.add_argument("--compute-target", default=os.getenv("MLOPS_COMPUTE_TARGET"))
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

    try:
        upload_run_outputs(
            run_dir=Path(args.run_dir),
            storage_account=args.storage_account,
            environment=args.environment,
            run_owner=args.run_owner,
            compute_target=args.compute_target,
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
        print(f"upload failed: {exc}", file=sys.stderr)
        return 1

    print(f"upload succeeded: run_dir={args.run_dir}")
    return 0


def upload_run_outputs(
    run_dir: Path,
    storage_account: str,
    environment: str,
    run_owner: str,
    containers: dict[str, str],
    compute_target: str | None = None,
    runner: Runner | None = None,
) -> None:
    command_runner = runner or _run_command
    plan = build_upload_plan(
        run_dir=run_dir,
        environment=environment,
        run_owner=run_owner,
        compute_target=compute_target,
        containers=containers,
    )

    for target in plan.values():
        print(
            "upload plan: "
            f"container={target.container} "
            f"blob_path={target.blob_path} "
            f"source={target.source}"
        )
        command_runner(
            [
                "az",
                "storage",
                "blob",
                "upload",
                "--account-name",
                storage_account,
                "--container-name",
                target.container,
                "--name",
                target.blob_path,
                "--file",
                str(target.source),
                "--auth-mode",
                "login",
                "--overwrite",
                "true",
            ]
        )


def build_upload_plan(
    run_dir: Path,
    environment: str,
    run_owner: str = "team46",
    compute_target: str | None = None,
    trigger_type: str | None = None,
    containers: dict[str, str] | None = None,
) -> dict[str, UploadTarget]:
    resolved_run_dir = Path(run_dir)
    if not resolved_run_dir.exists():
        raise FileNotFoundError(f"run directory not found: {resolved_run_dir}")
    run_id = _run_id_from_log(resolved_run_dir)
    manifest = manifest_from_run_dir(resolved_run_dir, run_id)
    for artifact in manifest.artifacts:
        if not artifact.local_path.exists():
            raise FileNotFoundError(f"required run artifact not found: {artifact.local_path}")
    layout = ArtifactLayout.default(containers)
    targets = layout.blob_targets(
        manifest,
        RunPartition(
            environment=environment,
            owner=run_owner,
            compute_target=compute_target,
            trigger_type=trigger_type,
            run_id=run_id,
        ),
    )
    return {
        _legacy_plan_key(logical_name): UploadTarget(
            source=target.local_path,
            container=target.container,
            blob_path=target.blob_path,
        )
        for logical_name, target in targets.items()
    }


def publish_run_outputs_with_blob_sink(
    run_dir: Path,
    blob_service,
    environment: str,
    run_owner: str,
    containers: dict[str, str],
    compute_target: str | None = None,
    trigger_type: str | None = None,
):
    run_log = _run_log(Path(run_dir))
    metadata = _metadata_from_log(run_log)
    run_result = RunResult(
        metadata=metadata,
        manifest=manifest_from_run_dir(Path(run_dir), metadata.run_id),
        run_dir=Path(run_dir),
    )
    partition = RunPartition(
        environment=environment,
        owner=run_owner,
        run_id=metadata.run_id,
        compute_target=compute_target,
        trigger_type=trigger_type,
    )
    return AzureBlobArtifactSink(
        blob_service=blob_service,
        layout=ArtifactLayout.default(containers),
        partition=partition,
    ).publish(run_result)


def _run_id_from_log(run_dir: Path) -> str:
    run_log = _run_log(run_dir)
    if run_log.get("run_id"):
        return str(run_log["run_id"])
    return run_dir.name


def _run_log(run_dir: Path) -> dict[str, object]:
    run_log_path = run_dir / "model_run_log.json"
    if run_log_path.exists():
        return json.loads(run_log_path.read_text())
    return {}


def _metadata_from_log(run_log: dict[str, object]) -> RunMetadata:
    return RunMetadata(
        run_id=str(run_log["run_id"]),
        status=str(run_log.get("status", "unknown")),
        row_count=int(run_log.get("row_count", 0)),
        validation_status=str(run_log.get("validation_status", "unknown")),
        drift_status=str(run_log.get("drift_status", "unknown")),
        started_at_utc=str(run_log.get("started_at_utc", "")),
        finished_at_utc=str(run_log.get("finished_at_utc", "")),
        model_version=str(run_log.get("model_version", "")),
        logic_version=str(run_log.get("logic_version", "")),
        environment=_optional_str(run_log.get("environment")),
        owner=_optional_str(run_log.get("owner")),
        trigger_type=_optional_str(run_log.get("trigger_type")),
        input_blob_path=_optional_str(run_log.get("input_blob_path")),
        git_commit_hash=_optional_str(run_log.get("git_commit_hash")),
        model_repo=_optional_str(run_log.get("model_repo")),
        model_ref=_optional_str(run_log.get("model_ref")),
        model_commit_sha=_optional_str(run_log.get("model_commit_sha")),
    )


def _legacy_plan_key(logical_name: str) -> str:
    return {
        "curated_dataset": "curated",
        "curated_artifact": "artifacts",
        "model_run_log": "runs",
        "model_output_snapshot": "snapshots",
        "model_drift_log": "drift-logs",
        "report": "reports",
    }[logical_name]


def _optional_str(value: object) -> str | None:
    return str(value) if value is not None else None


def _run_command(command: list[str]) -> None:
    subprocess.run(command, check=True)


if __name__ == "__main__":
    raise SystemExit(main())
