from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class RunMetadata:
    run_id: str
    status: str
    row_count: int
    validation_status: str
    drift_status: str
    started_at_utc: str
    finished_at_utc: str
    model_version: str
    logic_version: str
    input_blob_path: str | None = None
    environment: str | None = None
    owner: str | None = None
    trigger_type: str | None = None
    dataset_version: str = "local-sample"
    schema_version: str = "pricing_input_schema_v1"
    config_version: str = "pricing_rules_config_v1"
    git_commit_hash: str | None = None
    model_repo: str | None = None
    model_ref: str | None = None
    model_commit_sha: str | None = None
    extra: Mapping[str, object] = field(default_factory=dict)

    def with_extra(self, values: Mapping[str, object]) -> RunMetadata:
        return replace(self, extra=MappingProxyType({**self.extra, **values}))

    def to_log_dict(self, output_path: str | None, artifacts: Mapping[str, str]) -> dict[str, object]:
        payload: dict[str, object] = {
            "run_id": self.run_id,
            "status": self.status,
            "row_count": self.row_count,
            "validation_status": self.validation_status,
            "drift_status": self.drift_status,
            "started_at_utc": self.started_at_utc,
            "finished_at_utc": self.finished_at_utc,
            "dataset_version": self.dataset_version,
            "schema_version": self.schema_version,
            "model_version": self.model_version,
            "logic_version": self.logic_version,
            "config_version": self.config_version,
            "git_commit_hash": self.git_commit_hash,
            "artifacts": dict(artifacts),
        }
        if output_path:
            payload["output_path"] = output_path
        optional = {
            "environment": self.environment,
            "owner": self.owner,
            "trigger_type": self.trigger_type,
            "input_blob_path": self.input_blob_path,
            "model_repo": self.model_repo,
            "model_ref": self.model_ref,
            "model_commit_sha": self.model_commit_sha,
        }
        payload.update({key: value for key, value in optional.items() if value is not None})
        payload.update(dict(self.extra))
        return payload


@dataclass(frozen=True)
class RunArtifact:
    logical_name: str
    filename: str
    local_path: Path
    content_type: str
    required: bool = True


@dataclass(frozen=True)
class ArtifactManifest:
    run_id: str
    artifacts: tuple[RunArtifact, ...]
    schema_version: str = "artifact_manifest_v1"

    def by_logical_name(self) -> dict[str, RunArtifact]:
        return {artifact.logical_name: artifact for artifact in self.artifacts}

    def artifact_filenames(self) -> dict[str, str]:
        return {artifact.logical_name: artifact.filename for artifact in self.artifacts}


@dataclass(frozen=True)
class RunResult:
    metadata: RunMetadata
    manifest: ArtifactManifest
    run_dir: Path | None = None

    @property
    def run_id(self) -> str:
        return self.metadata.run_id

    @property
    def row_count(self) -> int:
        return self.metadata.row_count
