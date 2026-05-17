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
    containers: dict[str, str] | None = None,
) -> dict[str, UploadTarget]:
    resolved_run_dir = Path(run_dir)
    if not resolved_run_dir.exists():
        raise FileNotFoundError(f"run directory not found: {resolved_run_dir}")

    container_map = containers or {
        "runs": "runs",
        "curated": "curated",
        "snapshots": "snapshots",
        "drift_logs": "drift-logs",
        "reports": "reports",
        "artifacts": "artifacts",
    }
    run_id = _run_id_from_log(resolved_run_dir)
    run_date = run_id[:8] if len(run_id) >= 8 else "unknown"
    prefix_parts = [f"environment={environment}"]
    if compute_target:
        prefix_parts.append(f"compute={compute_target}")
    prefix_parts.extend(
        [
            f"owner={run_owner}",
            f"run_date={run_date}",
            f"run_id={run_id}",
        ]
    )
    prefix = "/".join(prefix_parts)

    files = {
        "curated": "curated_pricing.csv",
        "runs": "model_run_log.json",
        "snapshots": "model_output_snapshot.csv",
        "drift-logs": "model_drift_log.json",
        "reports": "report.md",
        "artifacts": "curated_pricing.csv",
    }
    mapped_containers = {
        "curated": container_map["curated"],
        "runs": container_map["runs"],
        "snapshots": container_map["snapshots"],
        "drift-logs": container_map["drift_logs"],
        "reports": container_map["reports"],
        "artifacts": container_map["artifacts"],
    }

    plan: dict[str, UploadTarget] = {}
    for logical_container, filename in files.items():
        source = resolved_run_dir / filename
        if not source.exists():
            raise FileNotFoundError(f"required run artifact not found: {source}")
        plan[logical_container] = UploadTarget(
            source=source,
            container=mapped_containers[logical_container],
            blob_path=f"{prefix}/{filename}",
        )
    return plan


def _run_id_from_log(run_dir: Path) -> str:
    run_log_path = run_dir / "model_run_log.json"
    if run_log_path.exists():
        run_log = json.loads(run_log_path.read_text())
        if run_log.get("run_id"):
            return str(run_log["run_id"])
    return run_dir.name


def _run_command(command: list[str]) -> None:
    subprocess.run(command, check=True)


if __name__ == "__main__":
    raise SystemExit(main())
