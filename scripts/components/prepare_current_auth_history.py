#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from pricing_mlops.monitoring.pipeline.steps.prepare_current_auth_history import (  # noqa: E402
    prepare_current_auth_history,
)
from scripts.components.storage_io import download_blob, upload_tree  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build current AUTH history snapshot from masked pricing input.")
    parser.add_argument("--storage-account", required=True)
    parser.add_argument("--input-container", default="raw-masked")
    parser.add_argument("--input-blob-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--current-history-container", default="")
    parser.add_argument("--current-history-prefix", default="")
    args = parser.parse_args()

    try:
        output_dir = Path(args.output_dir)
        input_path = output_dir.parent / "_downloaded_current_history" / "current_history_input.csv"
        download_blob(args.storage_account, args.input_container, args.input_blob_path, input_path)
        prepare_local_current_history(input_path=input_path, output_dir=output_dir, run_id=args.run_id)
        if args.current_history_container and args.current_history_prefix:
            upload_tree(
                args.storage_account,
                args.current_history_container,
                args.current_history_prefix,
                output_dir,
            )
    except Exception as exc:
        print(f"prepare_current_auth_history failed: {exc}", file=sys.stderr)
        return 1
    return 0


def prepare_local_current_history(input_path: Path, output_dir: Path, run_id: str) -> None:
    prepare_current_auth_history(input_path=input_path, output_dir=output_dir, run_id=run_id)


if __name__ == "__main__":
    raise SystemExit(main())
