#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from pricing_mlops.monitoring.pipeline.registry import (  # noqa: E402
    get_monitoring_step,
    monitoring_step_slugs,
    run_registered_step,
)
from scripts.components.storage_io import download_blob, download_tree, upload_tree  # noqa: E402


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    definition = get_monitoring_step(args.step)

    try:
        _materialize_inputs(definition, args)
        result = run_registered_step(
            definition,
            input_dir=Path(args.input_dir) if args.input_dir else None,
            output_dir=Path(args.output_dir) if args.output_dir else None,
            run_id=args.run_id,
            baseline_snapshot_path=Path(args.baseline_snapshot_path) if args.baseline_snapshot_path else None,
            current_history_path=Path(args.current_history_path) if args.current_history_path else None,
        )
        _publish_outputs(definition, args)
    except Exception as exc:
        print(f"{definition.slug} failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(definition.summary(result), indent=2, sort_keys=True))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a registered AUTH monitoring pipeline step.")
    parser.add_argument("--step", required=True, choices=monitoring_step_slugs())
    parser.add_argument("--input-dir", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--storage-account", default="")
    parser.add_argument("--baseline-snapshot-path", default="")
    parser.add_argument("--current-history-path", default="")
    parser.add_argument("--baseline-snapshot-container", default="")
    parser.add_argument("--baseline-snapshot-blob-path", default="")
    parser.add_argument("--current-history-container", default="")
    parser.add_argument("--current-history-blob-path", default="")
    parser.add_argument("--monitoring-inputs-container", default="")
    parser.add_argument("--monitoring-inputs-prefix", default="")
    parser.add_argument("--validity-container", default="")
    parser.add_argument("--validity-prefix", default="")
    parser.add_argument("--drift-container", default="")
    parser.add_argument("--drift-prefix", default="")
    parser.add_argument("--decision-container", default="")
    parser.add_argument("--decision-prefix", default="")
    parser.add_argument("--handoff-container", default="")
    parser.add_argument("--handoff-prefix", default="")
    return parser


def _materialize_inputs(definition, args: argparse.Namespace) -> None:
    if definition.uses_snapshot_inputs:
        _download_snapshot_inputs(definition, args)
        return
    if not args.storage_account or not definition.state_container_arg or not definition.state_prefix_arg:
        return
    container = getattr(args, definition.state_container_arg)
    prefix = getattr(args, definition.state_prefix_arg)
    if container and prefix:
        download_tree(args.storage_account, container, prefix, Path(args.input_dir or definition.input_dir))


def _download_snapshot_inputs(definition, args: argparse.Namespace) -> None:
    if args.storage_account and args.baseline_snapshot_container and args.baseline_snapshot_blob_path:
        baseline_path = Path(args.baseline_snapshot_path or definition.baseline_snapshot_path)
        download_blob(
            args.storage_account,
            args.baseline_snapshot_container,
            args.baseline_snapshot_blob_path,
            baseline_path,
        )
    if args.storage_account and args.current_history_container and args.current_history_blob_path:
        current_history_path = Path(args.current_history_path or definition.current_history_path)
        download_blob(
            args.storage_account,
            args.current_history_container,
            args.current_history_blob_path,
            current_history_path,
        )


def _publish_outputs(definition, args: argparse.Namespace) -> None:
    if not args.storage_account or not definition.publish_container_arg or not definition.publish_prefix_arg:
        return
    container = getattr(args, definition.publish_container_arg)
    prefix = getattr(args, definition.publish_prefix_arg)
    if container and prefix:
        upload_tree(args.storage_account, container, prefix, Path(args.output_dir or definition.output_dir))


if __name__ == "__main__":
    raise SystemExit(main())
