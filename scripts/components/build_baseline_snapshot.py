#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from pricing.baseline import build_baseline_snapshot  # noqa: E402
from scripts.components.storage_io import download_blob, upload_tree  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build model_output_snapshot baseline from approved feature table.")
    parser.add_argument("--storage-account", required=True)
    parser.add_argument("--feature-table-container", default="curated")
    parser.add_argument("--feature-table-blob-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--baseline-container", default="")
    parser.add_argument("--baseline-prefix", default="")
    args = parser.parse_args()

    try:
        output_dir = Path(args.output_dir)
        feature_table_path = output_dir.parent / "_downloaded_baseline" / "feature_table.csv"
        download_blob(
            args.storage_account,
            args.feature_table_container,
            args.feature_table_blob_path,
            feature_table_path,
        )
        build_local_baseline_snapshot(
            feature_table_path=feature_table_path,
            output_dir=output_dir,
            run_id=args.run_id,
        )
        if args.baseline_container and args.baseline_prefix:
            upload_tree(args.storage_account, args.baseline_container, args.baseline_prefix, output_dir)
    except Exception as exc:
        print(f"build_baseline_snapshot failed: {exc}", file=sys.stderr)
        return 1
    return 0


def build_local_baseline_snapshot(feature_table_path: Path, output_dir: Path, run_id: str) -> None:
    build_baseline_snapshot(
        feature_table_path=feature_table_path,
        output_path=output_dir / "snapshots" / "model_output_snapshot.csv",
        run_id=run_id,
    )


if __name__ == "__main__":
    raise SystemExit(main())
