#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from pricing_mlops.monitoring.pipeline.steps.build_monitoring_inputs import build_monitoring_inputs
from scripts.components.storage_io import download_blob, upload_tree


def main() -> int:
    parser = argparse.ArgumentParser(description="Build AUTH monitoring input snapshots.")
    parser.add_argument("--baseline-snapshot-path", required=True)
    parser.add_argument("--current-history-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--storage-account", default="")
    parser.add_argument("--baseline-snapshot-container", default="")
    parser.add_argument("--baseline-snapshot-blob-path", default="")
    parser.add_argument("--current-history-container", default="")
    parser.add_argument("--current-history-blob-path", default="")
    parser.add_argument("--monitoring-inputs-container", default="")
    parser.add_argument("--monitoring-inputs-prefix", default="")
    args = parser.parse_args()

    try:
        baseline_snapshot_path = Path(args.baseline_snapshot_path)
        current_history_path = Path(args.current_history_path)
        if args.storage_account and args.baseline_snapshot_container and args.baseline_snapshot_blob_path:
            baseline_snapshot_path = Path(args.output_dir) / "_inputs" / "baseline_recommendation_snapshot.csv"
            download_blob(
                args.storage_account,
                args.baseline_snapshot_container,
                args.baseline_snapshot_blob_path,
                baseline_snapshot_path,
            )
        if args.storage_account and args.current_history_container and args.current_history_blob_path:
            current_history_path = Path(args.output_dir) / "_inputs" / "current_auth_history_snapshot_real.csv"
            download_blob(
                args.storage_account,
                args.current_history_container,
                args.current_history_blob_path,
                current_history_path,
            )
        result = build_monitoring_inputs(
            baseline_snapshot_path=baseline_snapshot_path,
            current_history_path=current_history_path,
            output_dir=args.output_dir,
            run_id=args.run_id,
        )
        if args.storage_account and args.monitoring_inputs_container and args.monitoring_inputs_prefix:
            upload_tree(
                args.storage_account,
                args.monitoring_inputs_container,
                args.monitoring_inputs_prefix,
                Path(args.output_dir),
            )
    except Exception as exc:
        print(f"build_monitoring_inputs failed: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "output_dir": str(result.output_dir),
                "recommendation_price_column": result.recommendation_price_column,
                "row_counts": result.row_counts,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
