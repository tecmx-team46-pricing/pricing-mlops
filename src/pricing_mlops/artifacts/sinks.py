from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
from typing import Any

from pricing_mlops.artifacts.layout import ArtifactLayout, RunPartition
from pricing_mlops.artifacts.models import RunResult
from pricing_mlops.artifacts.publishing import PublishStatus, SinkPublishResult
from pricing_mlops.artifacts.retry import RetryPolicy


@dataclass(frozen=True)
class LocalArtifactSink:
    root: Path
    required: bool = True
    name: str = "local"

    def publish(self, run_result: RunResult) -> SinkPublishResult:
        target_dir = self.root / run_result.run_id
        target_dir.mkdir(parents=True, exist_ok=True)
        published: dict[str, str] = {}
        failed: dict[str, str] = {}
        for artifact in run_result.manifest.artifacts:
            destination = target_dir / artifact.filename
            try:
                shutil.copyfile(artifact.local_path, destination)
                published[artifact.logical_name] = str(destination)
            except Exception as exc:
                failed[artifact.logical_name] = str(exc)
                if artifact.required:
                    break
        return _sink_result(self.name, published, failed, manifest_uri=str(target_dir))


@dataclass(frozen=True)
class AzureBlobArtifactSink:
    blob_service: Any
    layout: ArtifactLayout
    partition: RunPartition
    retry_policy: RetryPolicy = RetryPolicy()
    required: bool = True
    name: str = "azure_blob"
    overwrite: bool = True

    def publish(self, run_result: RunResult) -> SinkPublishResult:
        published: dict[str, str] = {}
        failed: dict[str, str] = {}
        for logical_name, target in self.layout.blob_targets(run_result.manifest, self.partition).items():
            try:
                blob_client = self.blob_service.get_blob_client(
                    container=target.container,
                    blob=target.blob_path,
                )
                with target.local_path.open("rb") as handle:
                    self.retry_policy.run(lambda: blob_client.upload_blob(handle, overwrite=self.overwrite))
                published[logical_name] = f"azureblob://{target.container}/{target.blob_path}"
            except Exception as exc:
                failed[logical_name] = str(exc)
                if target.required:
                    break
        manifest_uri = published.get("model_run_log")
        return _sink_result(self.name, published, failed, manifest_uri=manifest_uri)


@dataclass(frozen=True)
class AzureMlArtifactSink:
    tracking_client: Any
    required: bool = False
    name: str = "azure_ml"

    def publish(self, run_result: RunResult) -> SinkPublishResult:
        metadata = run_result.metadata
        published: dict[str, str] = {}
        failed: dict[str, str] = {}
        tags = {
            "run_id": metadata.run_id,
            "status": metadata.status,
            "environment": metadata.environment,
            "owner": metadata.owner,
            "trigger_type": metadata.trigger_type,
            "input_blob_path": metadata.input_blob_path,
            "model_version": metadata.model_version,
            "model_repo": metadata.model_repo,
            "model_ref": metadata.model_ref,
            "model_commit_sha": metadata.model_commit_sha,
        }
        try:
            for key, value in tags.items():
                if value is not None:
                    self.tracking_client.set_tag(key, value)
            self.tracking_client.log_metric("row_count", metadata.row_count)
            for artifact in run_result.manifest.artifacts:
                self.tracking_client.set_tag(f"artifact.{artifact.logical_name}", artifact.filename)
                published[artifact.logical_name] = artifact.filename
        except Exception as exc:
            failed["azure_ml"] = str(exc)
        return _sink_result(self.name, published, failed)


@dataclass(frozen=True)
class SqlRunMetadataSink:
    connection: Any
    table_name: str = "pricing_run_metadata"
    required: bool = False
    name: str = "sql_metadata"

    def publish(self, run_result: RunResult) -> SinkPublishResult:
        metadata = run_result.metadata
        artifact_manifest_uri = _manifest_uri(run_result)
        publish_status = metadata.status
        payload = {
            "run_id": metadata.run_id,
            "environment": metadata.environment,
            "owner": metadata.owner,
            "status": metadata.status,
            "row_count": metadata.row_count,
            "drift_status": metadata.drift_status,
            "started_at_utc": metadata.started_at_utc,
            "finished_at_utc": metadata.finished_at_utc,
            "model_version": metadata.model_version,
            "input_blob_path": metadata.input_blob_path,
            "artifact_manifest_uri": artifact_manifest_uri,
            "publish_status": publish_status,
        }
        try:
            self.connection.execute(_upsert_sql(self.table_name), payload)
            self.connection.commit()
        except Exception as exc:
            return SinkPublishResult(self.name, PublishStatus.FAILED, failed={"sql": str(exc)})
        return SinkPublishResult(
            self.name,
            PublishStatus.SUCCEEDED,
            published={"metadata": metadata.run_id},
            manifest_uri=artifact_manifest_uri,
        )


def _sink_result(
    name: str,
    published: dict[str, str],
    failed: dict[str, str],
    manifest_uri: str | None = None,
) -> SinkPublishResult:
    if failed and published:
        status = PublishStatus.PARTIAL
    elif failed:
        status = PublishStatus.FAILED
    else:
        status = PublishStatus.SUCCEEDED
    return SinkPublishResult(name, status, published=published, failed=failed, manifest_uri=manifest_uri)


def _manifest_uri(run_result: RunResult) -> str:
    if run_result.run_dir:
        return str(run_result.run_dir / "model_run_log.json")
    return json.dumps(run_result.manifest.artifact_filenames(), sort_keys=True)


def _upsert_sql(table_name: str) -> str:
    return f"""
insert into {table_name} (
    run_id, environment, owner, status, row_count, drift_status,
    started_at_utc, finished_at_utc, model_version, input_blob_path,
    artifact_manifest_uri, publish_status
) values (
    :run_id, :environment, :owner, :status, :row_count, :drift_status,
    :started_at_utc, :finished_at_utc, :model_version, :input_blob_path,
    :artifact_manifest_uri, :publish_status
)
on conflict(run_id) do update set
    environment = excluded.environment,
    owner = excluded.owner,
    status = excluded.status,
    row_count = excluded.row_count,
    drift_status = excluded.drift_status,
    started_at_utc = excluded.started_at_utc,
    finished_at_utc = excluded.finished_at_utc,
    model_version = excluded.model_version,
    input_blob_path = excluded.input_blob_path,
    artifact_manifest_uri = excluded.artifact_manifest_uri,
    publish_status = excluded.publish_status
""".strip()
