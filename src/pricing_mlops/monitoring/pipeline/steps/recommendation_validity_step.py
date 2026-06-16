from __future__ import annotations

from pathlib import Path

from pricing_mlops.io.csv import read_csv_rows, write_csv_rows
from pricing_mlops.io.filesystem import copy_tree
from pricing.auth_monitoring.config import AuthMonitoringConfig
from pricing.auth_monitoring.rules.recommendation_validity import (
    RecommendationValidityResult,
    calculate_recommendation_validity,
)


def run_recommendation_validity_step(
    *,
    input_dir: str | Path,
    output_dir: str | Path,
    config: AuthMonitoringConfig | None = None,
) -> RecommendationValidityResult:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    copy_tree(input_dir, output_dir)
    snapshots_dir = input_dir / "snapshots"
    result = calculate_recommendation_validity(
        baseline_recommendation_snapshot=read_csv_rows(snapshots_dir / "baseline_recommendation_snapshot.csv"),
        baseline_auth_history_profile=read_csv_rows(snapshots_dir / "baseline_auth_history_profile.csv"),
        current_auth_history=read_csv_rows(snapshots_dir / "current_auth_history_snapshot_real.csv"),
        config=config,
    )
    write_csv_rows(output_dir / "logs" / "auth_recommendation_validity_log.csv", result.validity_log)
    write_csv_rows(output_dir / "logs" / "new_combo_without_baseline_recommendation_log.csv", result.new_combo_log)
    write_csv_rows(output_dir / "summaries" / "validity_summary.csv", result.validity_summary)
    write_csv_rows(output_dir / "summaries" / "validity_revenue_summary.csv", result.validity_revenue_summary)
    write_csv_rows(output_dir / "summaries" / "validity_reason_summary.csv", result.validity_reason_summary)
    return result
