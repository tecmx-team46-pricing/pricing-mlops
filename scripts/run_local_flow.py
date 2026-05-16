#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pricing_mlops.run import run_local_flow


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local Pricing MLOps flow.")
    parser.add_argument("--input", required=True, help="Path to masked or synthetic CSV input.")
    parser.add_argument("--output", required=True, help="Output root for local run artifacts.")
    args = parser.parse_args()

    try:
        result = run_local_flow(input_path=args.input, output_root=args.output)
    except Exception as exc:
        print(f"local flow failed: {exc}", file=sys.stderr)
        return 1

    print(f"local flow succeeded: run_id={result.run_id} output={result.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
