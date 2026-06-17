#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pricing.preparation import read_csv_records
from pricing.preparation.validation import validate_pricing_input


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Pricing MLOps input CSV.")
    parser.add_argument("--input", required=True, help="Path to masked or synthetic CSV input.")
    args = parser.parse_args()

    try:
        records = read_csv_records(args.input)
        result = validate_pricing_input(records)
    except Exception as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 2

    print(f"validation passed: rows={result.row_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
