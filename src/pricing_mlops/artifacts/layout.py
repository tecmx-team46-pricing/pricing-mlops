from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pricing_mlops.artifacts.models import ArtifactManifest, RunArtifact, RunMetadata


ARTIFACT_FILES = {
    "curated_dataset": "curated_pricing.csv",
    "model_output_snapshot": "model_output_snapshot.csv",
    "model_drift_log": "model_drift_log.json",
    "model_run_log": "model_run_log.json",
    "report": "report.md",
}


@dataclass(frozen=True)
class RunPartition:
    environment: str
    owner: str
    run_id: str
    compute_target: str | None = None
    trigger_type: str | None = None

    @property
    def run_date(self) -> str:
        return self.run_id[:8] if len(self.run_id) >= 8 else "unknown"


@dataclass(frozen=True)
class LayoutPolicy:
    include_compute_target: bool = True
    include_trigger_type: bool = True


@dataclass(frozen=True)
class ArtifactTarget:
    logical_name: str
    local_path: Path
    container: str
    blob_path: str
    required: bool = True


@dataclass(frozen=True)
class ArtifactLayout:
    containers: dict[str, str]
    policy: LayoutPolicy = LayoutPolicy()

    @classmethod
    def default(cls, containers: dict[str, str] | None = None) -> ArtifactLayout:
        return cls(
            containers=containers
            or {
                "runs": "runs",
                "curated": "curated",
                "snapshots": "snapshots",
                "drift_logs": "drift-logs",
                "reports": "reports",
                "artifacts": "artifacts",
            }
        )

    def partition_prefix(self, partition: RunPartition) -> str:
        parts = [f"environment={partition.environment}"]
        if self.policy.include_compute_target and partition.compute_target:
            parts.append(f"compute={partition.compute_target}")
        if self.policy.include_trigger_type and partition.trigger_type:
            parts.append(f"trigger={partition.trigger_type}")
        parts.extend(
            [
                f"owner={partition.owner}",
                f"run_date={partition.run_date}",
                f"run_id={partition.run_id}",
            ]
        )
        return "/".join(parts)

    def blob_targets(self, manifest: ArtifactManifest, partition: RunPartition) -> dict[str, ArtifactTarget]:
        artifacts = manifest.by_logical_name()
        prefix = self.partition_prefix(partition)
        mappings = {
            "curated_dataset": ("curated", ARTIFACT_FILES["curated_dataset"]),
            "model_run_log": ("runs", ARTIFACT_FILES["model_run_log"]),
            "model_output_snapshot": ("snapshots", ARTIFACT_FILES["model_output_snapshot"]),
            "model_drift_log": ("drift_logs", ARTIFACT_FILES["model_drift_log"]),
            "report": ("reports", ARTIFACT_FILES["report"]),
            "curated_artifact": ("artifacts", ARTIFACT_FILES["curated_dataset"]),
        }

        targets: dict[str, ArtifactTarget] = {}
        for logical_name, (container_key, filename) in mappings.items():
            source_artifact = artifacts["curated_dataset"] if logical_name == "curated_artifact" else artifacts[logical_name]
            targets[logical_name] = ArtifactTarget(
                logical_name=logical_name,
                local_path=source_artifact.local_path,
                container=self.containers[container_key],
                blob_path=f"{prefix}/{filename}",
                required=source_artifact.required,
            )
        return targets


def manifest_from_run_dir(run_dir: Path, run_id: str) -> ArtifactManifest:
    artifacts = (
        RunArtifact("curated_dataset", ARTIFACT_FILES["curated_dataset"], run_dir / ARTIFACT_FILES["curated_dataset"], "text/csv"),
        RunArtifact(
            "model_output_snapshot",
            ARTIFACT_FILES["model_output_snapshot"],
            run_dir / ARTIFACT_FILES["model_output_snapshot"],
            "text/csv",
        ),
        RunArtifact(
            "model_drift_log",
            ARTIFACT_FILES["model_drift_log"],
            run_dir / ARTIFACT_FILES["model_drift_log"],
            "application/json",
        ),
        RunArtifact(
            "model_run_log",
            ARTIFACT_FILES["model_run_log"],
            run_dir / ARTIFACT_FILES["model_run_log"],
            "application/json",
        ),
        RunArtifact("report", ARTIFACT_FILES["report"], run_dir / ARTIFACT_FILES["report"], "text/markdown"),
    )
    return ArtifactManifest(run_id=run_id, artifacts=artifacts)


def partition_from_metadata(
    metadata: RunMetadata,
    environment: str,
    owner: str,
    compute_target: str | None = None,
    trigger_type: str | None = None,
) -> RunPartition:
    return RunPartition(
        environment=environment,
        owner=owner,
        run_id=metadata.run_id,
        compute_target=compute_target,
        trigger_type=trigger_type,
    )
