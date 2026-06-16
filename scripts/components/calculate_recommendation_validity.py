#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from pricing_mlops.monitoring.pipeline.steps.recommendation_validity_step import run_recommendation_validity_step
from scripts.components.storage_io import download_tree, upload_tree


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate AUTH recommendation validity against current history.")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--storage-account", default="")
    parser.add_argument("--monitoring-inputs-container", default="")
    parser.add_argument("--monitoring-inputs-prefix", default="")
    parser.add_argument("--validity-container", default="")
    parser.add_argument("--validity-prefix", default="")
    args = parser.parse_args()

    try:
        input_dir = Path(args.input_dir)
        if args.storage_account and args.monitoring_inputs_container and args.monitoring_inputs_prefix:
            download_tree(
                args.storage_account,
                args.monitoring_inputs_container,
                args.monitoring_inputs_prefix,
                input_dir,
            )
        result = run_recommendation_validity_step(input_dir=input_dir, output_dir=args.output_dir)
        if args.storage_account and args.validity_container and args.validity_prefix:
            upload_tree(args.storage_account, args.validity_container, args.validity_prefix, Path(args.output_dir))
    except Exception as exc:
        print(f"calculate_recommendation_validity failed: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "validity_rows": len(result.validity_log),
                "new_combo_rows": len(result.new_combo_log),
                "summary_rows": len(result.validity_summary),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
