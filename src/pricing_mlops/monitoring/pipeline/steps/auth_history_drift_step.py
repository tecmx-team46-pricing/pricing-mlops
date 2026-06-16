from __future__ import annotations

from pathlib import Path

from pricing_mlops.io.csv import read_csv_rows, write_csv_rows
from pricing_mlops.io.filesystem import copy_tree
from pricing.auth_monitoring.config import AuthMonitoringConfig
from pricing.auth_monitoring.rules.auth_history_drift import (
    AuthHistoryDriftResult,
    calculate_auth_history_drift,
)


def run_auth_history_drift_step(
    *,
    input_dir: str | Path,
    output_dir: str | Path,
    run_id: str,
    config: AuthMonitoringConfig | None = None,
) -> AuthHistoryDriftResult:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    copy_tree(input_dir, output_dir)
    snapshots_dir = input_dir / "snapshots"
    result = calculate_auth_history_drift(
        baseline_auth_history_profile=read_csv_rows(snapshots_dir / "baseline_auth_history_profile.csv"),
        current_auth_history=read_csv_rows(snapshots_dir / "current_auth_history_snapshot_real.csv"),
        run_id=run_id,
        config=config,
    )
    write_csv_rows(output_dir / "logs" / "auth_history_drift_log.csv", result.drift_log)
    return result
