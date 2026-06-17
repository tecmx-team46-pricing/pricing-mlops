#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from pricing.features import build_current_auth_features  # noqa: E402
from scripts.components.storage_io import download_blob, upload_tree  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build current AUTH features from masked pricing input.")
    parser.add_argument("--storage-account", required=True)
    parser.add_argument("--input-container", default="raw-masked")
    parser.add_argument("--input-blob-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--feature-container", default="")
    parser.add_argument("--feature-prefix", default="")
    args = parser.parse_args()

    try:
        output_dir = Path(args.output_dir)
        input_path = output_dir.parent / "_downloaded_feature_engineering" / "pricing_input.csv"
        download_blob(args.storage_account, args.input_container, args.input_blob_path, input_path)
        build_current_auth_features(input_path=input_path, output_dir=output_dir, run_id=args.run_id)
        if args.feature_container and args.feature_prefix:
            upload_tree(args.storage_account, args.feature_container, args.feature_prefix, output_dir)
    except Exception as exc:
        print(f"feature_engineering failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
