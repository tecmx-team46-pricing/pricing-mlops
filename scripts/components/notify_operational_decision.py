#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.components.storage_io import download_blob  # noqa: E402


REQUIRED_PAYLOAD_FIELDS = {
    "schema_version",
    "run_id",
    "severity",
    "should_notify",
    "blocking_decision",
    "title",
    "status",
    "recommended_operational_action",
    "primary_reason",
    "next_action_owner",
    "decision_rationale",
    "signals",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AUTH monitoring notification payload.")
    parser.add_argument("--storage-account", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--run-owner", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--trigger-type", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    try:
        summary = validate_published_notification_payload(
            storage_account=args.storage_account,
            environment=args.environment,
            run_owner=args.run_owner,
            run_id=args.run_id,
            trigger_type=args.trigger_type,
            output_dir=Path(args.output_dir),
        )
    except Exception as exc:
        print(f"notify_operational_decision failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def validate_published_notification_payload(
    *,
    storage_account: str,
    environment: str,
    run_owner: str,
    run_id: str,
    trigger_type: str,
    output_dir: Path,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload_path = output_dir / "notification_payload.json"
    blob_path = _notification_payload_blob_path(
        environment=environment,
        run_owner=run_owner,
        run_id=run_id,
        trigger_type=trigger_type,
    )
    download_blob(storage_account, "runs", blob_path, payload_path)
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_PAYLOAD_FIELDS - set(payload))
    if missing:
        raise ValueError(f"notification payload missing required field(s): {missing}")
    if payload["schema_version"] != "auth_monitoring_notification_v1":
        raise ValueError(f"unsupported notification payload schema: {payload['schema_version']}")
    if payload["run_id"] != run_id:
        raise ValueError(f"notification payload run_id mismatch: {payload['run_id']} != {run_id}")
    if not isinstance(payload["signals"], dict) or not payload["signals"]:
        raise ValueError("notification payload signals must be a non-empty object")

    summary = {
        "schema_version": "auth_monitoring_notification_smoke_v1",
        "run_id": payload["run_id"],
        "payload_blob": f"azureblob://runs/{blob_path}",
        "severity": payload["severity"],
        "status": payload["status"],
        "should_notify": payload["should_notify"],
        "blocking_decision": payload["blocking_decision"],
        "recommended_operational_action": payload["recommended_operational_action"],
        "next_action_owner": payload["next_action_owner"],
    }
    (output_dir / "notification_smoke_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _notification_payload_blob_path(
    *,
    environment: str,
    run_owner: str,
    run_id: str,
    trigger_type: str,
) -> str:
    return "/".join(
        [
            f"environment={environment}",
            "compute=azure-ml",
            f"trigger={trigger_type}",
            f"owner={run_owner}",
            f"run_date={run_id[:8] if len(run_id) >= 8 else 'unknown'}",
            f"run_id={run_id}",
            "summaries/notification_payload.json",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
