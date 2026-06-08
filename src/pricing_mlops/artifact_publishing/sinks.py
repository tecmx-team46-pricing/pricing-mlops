from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
from typing import Any

from pricing_mlops.artifact_publishing.layout import ArtifactLayout, RunPartition
from pricing_mlops.artifact_publishing.models import RunResult
from pricing_mlops.artifact_publishing.publishing import PublishStatus, SinkPublishResult
from pricing_mlops.artifact_publishing.retry import RetryPolicy


SQL_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$")


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
                self.retry_policy.run(lambda: _upload_local_file(blob_client, target.local_path, self.overwrite))
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
    retry_policy: RetryPolicy = RetryPolicy()
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
            self.retry_policy.run(lambda: _publish_azure_ml_metadata(self.tracking_client, tags, run_result))
            published = {artifact.logical_name: artifact.filename for artifact in run_result.manifest.artifacts}
        except Exception as exc:
            failed["azure_ml"] = str(exc)
        return _sink_result(self.name, published, failed)


@dataclass(frozen=True)
class SqlRunMetadataSink:
    connection: Any
    table_name: str = "model_run_log"
    snapshot_table_name: str = "model_output_snapshot_metadata"
    dialect: str = "sqlite"
    retry_policy: RetryPolicy = RetryPolicy()
    required: bool = False
    name: str = "sql_metadata"

    def publish(self, run_result: RunResult) -> SinkPublishResult:
        try:
            table_name = _validated_sql_identifier(self.table_name)
            snapshot_table_name = _validated_sql_identifier(self.snapshot_table_name)
        except ValueError as exc:
            return SinkPublishResult(self.name, PublishStatus.FAILED, failed={"sql": str(exc)})

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
            "trigger_type": metadata.trigger_type,
            "model_repo": metadata.model_repo,
            "model_ref": metadata.model_ref,
            "model_commit_sha": metadata.model_commit_sha,
        }
        snapshot_payload = {
            "run_id": metadata.run_id,
            "environment": metadata.environment,
            "snapshot_uri": _artifact_uri(run_result, "model_output_snapshot") or "",
            "row_count": metadata.row_count,
            "drift_status": metadata.drift_status,
            "output_schema_version": metadata.schema_version,
            "created_at_utc": metadata.finished_at_utc,
        }
        try:
            self.retry_policy.run(
                lambda: (
                    _upsert_metadata(self.connection, table_name, payload, self.dialect),
                    _upsert_snapshot_metadata(
                        self.connection,
                        snapshot_table_name,
                        snapshot_payload,
                        self.dialect,
                    ),
                    self.connection.commit(),
                )
            )
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


def _upload_local_file(blob_client, local_path: Path, overwrite: bool) -> None:
    with local_path.open("rb") as handle:
        blob_client.upload_blob(handle, overwrite=overwrite)


def _publish_azure_ml_metadata(tracking_client, tags: dict[str, object], run_result: RunResult) -> None:
    for key, value in tags.items():
        if value is not None:
            tracking_client.set_tag(key, value)
    tracking_client.log_metric("row_count", run_result.metadata.row_count)
    for artifact in run_result.manifest.artifacts:
        tracking_client.set_tag(f"artifact.{artifact.logical_name}", artifact.filename)


def _upsert_metadata(connection, table_name: str, payload: dict[str, object], dialect: str) -> None:
    _execute(connection, _run_log_upsert_sql(table_name, dialect), payload, dialect)


def _upsert_snapshot_metadata(connection, table_name: str, payload: dict[str, object], dialect: str) -> None:
    _execute(connection, _snapshot_upsert_sql(table_name, dialect), payload, dialect)


def _execute(connection, statement: str, payload: dict[str, object], dialect: str) -> None:
    if dialect == "sqlserver":
        columns = _sqlserver_parameters(statement)
        connection.execute(statement, tuple(payload[column] for column in columns))
        return
    connection.execute(statement, payload)


def _manifest_uri(run_result: RunResult) -> str:
    if run_result.run_dir:
        return str(run_result.run_dir / "model_run_log.json")
    return json.dumps(run_result.manifest.artifact_filenames(), sort_keys=True)


def _artifact_uri(run_result: RunResult, logical_name: str) -> str | None:
    artifact = run_result.manifest.by_logical_name().get(logical_name)
    if artifact is None:
        return None
    if run_result.run_dir:
        return str(artifact.local_path)
    return artifact.filename


def _run_log_upsert_sql(table_name: str, dialect: str) -> str:
    table_name = _validated_sql_identifier(table_name)
    if dialect == "sqlserver":
        return _sqlserver_merge_sql(
            table_name,
            key_column="run_id",
            columns=(
                "run_id",
                "environment",
                "owner",
                "status",
                "row_count",
                "drift_status",
                "started_at_utc",
                "finished_at_utc",
                "model_version",
                "input_blob_path",
                "artifact_manifest_uri",
                "publish_status",
                "trigger_type",
                "model_repo",
                "model_ref",
                "model_commit_sha",
            ),
        )
    return f"""
insert into {table_name} (
    run_id, environment, owner, status, row_count, drift_status,
    started_at_utc, finished_at_utc, model_version, input_blob_path,
    artifact_manifest_uri, publish_status, trigger_type, model_repo, model_ref,
    model_commit_sha
) values (
    :run_id, :environment, :owner, :status, :row_count, :drift_status,
    :started_at_utc, :finished_at_utc, :model_version, :input_blob_path,
    :artifact_manifest_uri, :publish_status, :trigger_type, :model_repo,
    :model_ref, :model_commit_sha
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
    publish_status = excluded.publish_status,
    trigger_type = excluded.trigger_type,
    model_repo = excluded.model_repo,
    model_ref = excluded.model_ref,
    model_commit_sha = excluded.model_commit_sha
""".strip()


def _snapshot_upsert_sql(table_name: str, dialect: str) -> str:
    table_name = _validated_sql_identifier(table_name)
    if dialect == "sqlserver":
        return _sqlserver_merge_sql(
            table_name,
            key_column="run_id",
            columns=(
                "run_id",
                "environment",
                "snapshot_uri",
                "row_count",
                "drift_status",
                "output_schema_version",
                "created_at_utc",
            ),
        )
    return f"""
insert into {table_name} (
    run_id, environment, snapshot_uri, row_count, drift_status,
    output_schema_version, created_at_utc
) values (
    :run_id, :environment, :snapshot_uri, :row_count, :drift_status,
    :output_schema_version, :created_at_utc
)
on conflict(run_id) do update set
    environment = excluded.environment,
    snapshot_uri = excluded.snapshot_uri,
    row_count = excluded.row_count,
    drift_status = excluded.drift_status,
    output_schema_version = excluded.output_schema_version,
    created_at_utc = excluded.created_at_utc
""".strip()


def _sqlserver_merge_sql(table_name: str, key_column: str, columns: tuple[str, ...]) -> str:
    table_name = _validated_sql_identifier(table_name)
    placeholders = ", ".join(f"? as {column}" for column in columns)
    update_columns = [column for column in columns if column != key_column]
    update_clause = ", ".join(f"target.{column} = source.{column}" for column in update_columns)
    insert_columns = ", ".join(columns)
    insert_values = ", ".join(f"source.{column}" for column in columns)
    return f"""
merge {table_name} as target
using (select {placeholders}) as source
on target.{key_column} = source.{key_column}
when matched then
  update set {update_clause}
when not matched then
  insert ({insert_columns})
  values ({insert_values});
""".strip()


def _validated_sql_identifier(identifier: str) -> str:
    if not SQL_IDENTIFIER_RE.fullmatch(identifier):
        raise ValueError(f"unsafe SQL identifier: {identifier}")
    return identifier


def _sqlserver_parameters(statement: str) -> tuple[str, ...]:
    select_clause = statement.split(") as source", 1)[0]
    return tuple(part.rsplit(" as ", 1)[1].strip() for part in select_clause.split("select ", 1)[1].split(", "))
