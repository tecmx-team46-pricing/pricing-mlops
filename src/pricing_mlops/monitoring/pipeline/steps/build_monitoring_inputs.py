from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from pricing.auth_monitoring.config import AuthMonitoringConfig, load_auth_monitoring_config


@dataclass(frozen=True)
class MonitoringInputsResult:
    output_dir: Path
    recommendation_price_column: str
    row_counts: dict[str, int]


def build_monitoring_inputs(
    baseline_snapshot_path: str | Path,
    current_history_path: str | Path,
    output_dir: str | Path,
    run_id: str,
    config: AuthMonitoringConfig | None = None,
) -> MonitoringInputsResult:
    cfg = config or load_auth_monitoring_config()
    baseline_rows = _read_csv(Path(baseline_snapshot_path))
    current_rows = _read_csv(Path(current_history_path))
    recommendation_column = _recommendation_column(baseline_rows, cfg)

    snapshots_dir = Path(output_dir) / "snapshots"
    manifest_dir = Path(output_dir) / "manifest"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    baseline_recommendations = _select_columns(
        baseline_rows,
        [*cfg.columns.key_columns, recommendation_column],
        rename={recommendation_column: "baseline_recommended_price"},
    )
    baseline_history = _select_columns(
        baseline_rows,
        [*cfg.columns.key_columns, *cfg.columns.baseline_history, *cfg.columns.global_bin],
    )
    current_history = _select_columns(current_rows, current_rows[0].keys() if current_rows else cfg.columns.key_columns)

    outputs = {
        "baseline_recommendation_snapshot": snapshots_dir / "baseline_recommendation_snapshot.csv",
        "baseline_auth_history_profile": snapshots_dir / "baseline_auth_history_profile.csv",
        "current_auth_history_snapshot_real": snapshots_dir / "current_auth_history_snapshot_real.csv",
    }
    _write_csv(outputs["baseline_recommendation_snapshot"], baseline_recommendations)
    _write_csv(outputs["baseline_auth_history_profile"], baseline_history)
    _write_csv(outputs["current_auth_history_snapshot_real"], current_history)
    _write_manifest(
        manifest_dir / "artifact_manifest.json",
        run_id=run_id,
        output_dir=Path(output_dir),
        artifacts=outputs,
    )
    return MonitoringInputsResult(
        output_dir=Path(output_dir),
        recommendation_price_column=recommendation_column,
        row_counts={
            "baseline_recommendations": len(baseline_recommendations),
            "baseline_auth_history": len(baseline_history),
            "current_auth_history": len(current_history),
        },
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _recommendation_column(rows: list[dict[str, str]], config: AuthMonitoringConfig) -> str:
    columns = set(rows[0].keys()) if rows else set()
    candidates = (
        *config.columns.official_recommendation_preferred,
        *config.columns.proxy_recommendation,
    )
    for column in candidates:
        if column in columns:
            return column
    raise ValueError(f"baseline snapshot is missing a recommendation column; tried {candidates}")


def _select_columns(
    rows: list[dict[str, str]],
    columns: object,
    rename: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    selected_columns = [column for column in columns if rows and column in rows[0]]
    rename = rename or {}
    return [
        {rename.get(column, column): row.get(column, "") for column in selected_columns}
        for row in rows
    ]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_manifest(
    path: Path,
    run_id: str,
    output_dir: Path,
    artifacts: dict[str, Path],
) -> None:
    records = [
        {
            "run_id": run_id,
            "logical_name": logical_name,
            "relative_path": artifact_path.relative_to(output_dir).as_posix(),
            "sha256": _sha256(artifact_path),
            "size_bytes": artifact_path.stat().st_size,
        }
        for logical_name, artifact_path in sorted(artifacts.items())
    ]
    path.write_text(
        json.dumps({"schema_version": "auth_monitoring_artifact_manifest_v1", "artifacts": records}, indent=2)
        + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
