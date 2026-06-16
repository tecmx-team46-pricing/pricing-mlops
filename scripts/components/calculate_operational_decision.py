#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from pricing_mlops.monitoring.pipeline.steps.operational_decision_step import run_operational_decision_step
from scripts.components.storage_io import download_tree, upload_tree


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate AUTH monitoring operational decision.")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--storage-account", default="")
    parser.add_argument("--validity-container", default="")
    parser.add_argument("--validity-prefix", default="")
    parser.add_argument("--decision-container", default="")
    parser.add_argument("--decision-prefix", default="")
    args = parser.parse_args()

    try:
        input_dir = Path(args.input_dir)
        if args.storage_account and args.validity_container and args.validity_prefix:
            download_tree(args.storage_account, args.validity_container, args.validity_prefix, input_dir)
        result = run_operational_decision_step(
            input_dir=input_dir,
            output_dir=args.output_dir,
            run_id=args.run_id,
        )
        if args.storage_account and args.decision_container and args.decision_prefix:
            upload_tree(args.storage_account, args.decision_container, args.decision_prefix, Path(args.output_dir))
    except Exception as exc:
        print(f"calculate_operational_decision failed: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "run_readiness_status": result.run_readiness_summary["run_readiness_status"],
                "recommended_operational_action": result.operational_decision_summary[
                    "recommended_operational_action"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
