from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class MonitoringArtifact:
    logical_name: str
    relative_path: Path
    platform_container_key: str
    content_type: str
    required: bool = True


@dataclass(frozen=True)
class MonitoringArtifactValidation:
    records: list[dict[str, object]]

    @property
    def missing_required(self) -> list[dict[str, object]]:
        return [record for record in self.records if record["required"] and not record["exists"]]

    @property
    def missing_optional(self) -> list[dict[str, object]]:
        return [record for record in self.records if not record["required"] and not record["exists"]]

    @property
    def is_complete(self) -> bool:
        return not self.missing_required


def expected_auth_monitoring_artifacts() -> dict[str, MonitoringArtifact]:
    return {
        artifact.logical_name: artifact
        for artifact in (
            MonitoringArtifact(
                "baseline_recommendation_snapshot",
                Path("snapshots/baseline_recommendation_snapshot.csv"),
                "snapshots",
                "text/csv",
            ),
            MonitoringArtifact(
                "baseline_auth_history_profile",
                Path("snapshots/baseline_auth_history_profile.csv"),
                "snapshots",
                "text/csv",
            ),
            MonitoringArtifact(
                "current_auth_history_snapshot_real",
                Path("snapshots/current_auth_history_snapshot_real.csv"),
                "snapshots",
                "text/csv",
            ),
            MonitoringArtifact(
                "auth_recommendation_validity_log",
                Path("logs/auth_recommendation_validity_log.csv"),
                "drift_logs",
                "text/csv",
            ),
            MonitoringArtifact(
                "auth_history_drift_log",
                Path("logs/auth_history_drift_log.csv"),
                "drift_logs",
                "text/csv",
            ),
            MonitoringArtifact(
                "operational_decision_summary",
                Path("summaries/operational_decision_summary.csv"),
                "runs",
                "text/csv",
            ),
            MonitoringArtifact(
                "notification_payload",
                Path("summaries/notification_payload.json"),
                "runs",
                "application/json",
            ),
            MonitoringArtifact(
                "simulated_operational_handoff",
                Path("summaries/simulated_operational_handoff.json"),
                "runs",
                "application/json",
            ),
            MonitoringArtifact(
                "run_readiness_summary",
                Path("summaries/run_readiness_summary.csv"),
                "runs",
                "text/csv",
            ),
            MonitoringArtifact(
                "auth_recommendation_validity_report",
                Path("reports/auth_recommendation_validity_report.md"),
                "reports",
                "text/markdown",
            ),
            MonitoringArtifact(
                "simulated_operational_handoff_report",
                Path("reports/simulated_operational_handoff.md"),
                "reports",
                "text/markdown",
            ),
            MonitoringArtifact(
                "artifact_manifest",
                Path("manifest/artifact_manifest.json"),
                "artifacts",
                "application/json",
            ),
        )
    }


def validate_expected_monitoring_artifacts(
    root: str | Path,
    artifacts: Mapping[str, MonitoringArtifact] | None = None,
) -> MonitoringArtifactValidation:
    root = Path(root)
    artifacts = artifacts or expected_auth_monitoring_artifacts()
    return MonitoringArtifactValidation(
        records=[
            {
                "logical_name": artifact.logical_name,
                "relative_path": artifact.relative_path.as_posix(),
                "platform_container_key": artifact.platform_container_key,
                "content_type": artifact.content_type,
                "required": artifact.required,
                "exists": (root / artifact.relative_path).is_file(),
            }
            for artifact in artifacts.values()
        ]
    )
