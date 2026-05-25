from __future__ import annotations

import sqlite3

from pricing_mlops.artifact_publishing import (
    ArtifactLayout,
    AzureBlobArtifactSink,
    AzureMlArtifactSink,
    LocalArtifactSink,
    PublishStatus,
    RunMetadata,
    RunPartition,
    RunResult,
    SqlRunMetadataSink,
)
from pricing_mlops.artifact_publishing.layout import manifest_from_run_dir
from pricing_mlops.artifact_publishing.retry import RetryPolicy


def test_local_artifact_sink_is_idempotent_for_same_run_id(tmp_path):
    run_result = _run_result(tmp_path)
    sink = LocalArtifactSink(root=tmp_path / "published")

    first = sink.publish(run_result)
    second = sink.publish(run_result)

    assert first.status == PublishStatus.SUCCEEDED
    assert second.status == PublishStatus.SUCCEEDED
    assert (tmp_path / "published" / run_result.run_id / "model_run_log.json").read_text() == "x"


def test_azure_blob_sink_uploads_current_layout_with_overwrite(tmp_path):
    run_result = _run_result(tmp_path)
    blob_service = _FakeBlobService()
    sink = AzureBlobArtifactSink(
        blob_service=blob_service,
        layout=ArtifactLayout.default(),
        partition=RunPartition(
            environment="staging",
            compute_target="azure-ml",
            trigger_type="manual",
            owner="team46",
            run_id=run_result.run_id,
        ),
    )

    result = sink.publish(run_result)

    assert result.status == PublishStatus.SUCCEEDED
    assert len(blob_service.uploads) == 6
    assert all(upload["overwrite"] is True for upload in blob_service.uploads)
    assert any(upload["container"] == "runs" and upload["blob"].endswith("model_run_log.json") for upload in blob_service.uploads)


def test_azure_blob_sink_retries_transient_upload_failure(tmp_path):
    run_result = _run_result(tmp_path)
    blob_service = _FlakyBlobService()
    sink = AzureBlobArtifactSink(
        blob_service=blob_service,
        layout=ArtifactLayout.default(),
        partition=RunPartition(
            environment="staging",
            compute_target="azure-ml",
            trigger_type="manual",
            owner="team46",
            run_id=run_result.run_id,
        ),
        retry_policy=RetryPolicy(attempts=2, delay_seconds=0),
    )

    result = sink.publish(run_result)

    assert result.status == PublishStatus.SUCCEEDED
    assert blob_service.attempts["curated/curated_pricing.csv"] == 2


def test_azure_ml_sink_records_metadata_and_artifact_references(tmp_path):
    run_result = _run_result(tmp_path)
    tracker = _FakeTracker()

    result = AzureMlArtifactSink(tracking_client=tracker).publish(run_result)

    assert result.status == PublishStatus.SUCCEEDED
    assert tracker.tags["run_id"] == run_result.run_id
    assert tracker.metrics["row_count"] == 1
    assert tracker.tags["artifact.model_run_log"] == "model_run_log.json"


def test_azure_ml_sink_retries_transient_tracking_failure(tmp_path):
    run_result = _run_result(tmp_path)
    tracker = _FlakyTracker()

    result = AzureMlArtifactSink(
        tracking_client=tracker,
        retry_policy=RetryPolicy(attempts=2, delay_seconds=0),
    ).publish(run_result)

    assert result.status == PublishStatus.SUCCEEDED
    assert tracker.failures == 1
    assert tracker.tags["run_id"] == run_result.run_id


def test_sql_run_metadata_sink_upserts_metadata(tmp_path):
    run_result = _run_result(tmp_path)
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        create table pricing_run_metadata (
            run_id text primary key,
            environment text,
            owner text,
            status text,
            row_count integer,
            drift_status text,
            started_at_utc text,
            finished_at_utc text,
            model_version text,
            input_blob_path text,
            artifact_manifest_uri text,
            publish_status text,
            trigger_type text,
            model_repo text,
            model_ref text,
            model_commit_sha text
        )
        """
    )
    _create_sqlite_snapshot_table(connection)
    sink = SqlRunMetadataSink(
        connection=connection,
        table_name="pricing_run_metadata",
        snapshot_table_name="model_output_snapshot_metadata",
    )

    first = sink.publish(run_result)
    second = sink.publish(run_result)

    assert first.status == PublishStatus.SUCCEEDED
    assert second.status == PublishStatus.SUCCEEDED
    count = connection.execute("select count(*) from pricing_run_metadata").fetchone()[0]
    assert count == 1
    row = connection.execute("select run_id, environment, row_count from pricing_run_metadata").fetchone()
    assert row == (run_result.run_id, "staging", 1)
    snapshot_row = connection.execute(
        "select run_id, output_schema_version from model_output_snapshot_metadata"
    ).fetchone()
    assert snapshot_row == (run_result.run_id, "pricing_input_schema_v1")


def test_sql_run_metadata_sink_retries_transient_upsert_failure(tmp_path):
    run_result = _run_result(tmp_path)
    connection = _FlakyConnection(sqlite3.connect(":memory:"))
    connection.execute(
        """
        create table pricing_run_metadata (
            run_id text primary key,
            environment text,
            owner text,
            status text,
            row_count integer,
            drift_status text,
            started_at_utc text,
            finished_at_utc text,
            model_version text,
            input_blob_path text,
            artifact_manifest_uri text,
            publish_status text,
            trigger_type text,
            model_repo text,
            model_ref text,
            model_commit_sha text
        )
        """
    )
    _create_sqlite_snapshot_table(connection)
    sink = SqlRunMetadataSink(
        connection=connection,
        table_name="pricing_run_metadata",
        snapshot_table_name="model_output_snapshot_metadata",
        retry_policy=RetryPolicy(attempts=2, delay_seconds=0),
    )

    result = sink.publish(run_result)

    assert result.status == PublishStatus.SUCCEEDED
    assert connection.failures == 1


def test_sql_run_metadata_sink_uses_sqlserver_merge_with_qmark_params(tmp_path):
    run_result = _run_result(tmp_path)
    connection = _RecordingConnection()
    sink = SqlRunMetadataSink(
        connection=connection,
        table_name="dbo.model_run_log",
        snapshot_table_name="dbo.model_output_snapshot_metadata",
        dialect="sqlserver",
    )

    result = sink.publish(run_result)

    assert result.status == PublishStatus.SUCCEEDED
    assert connection.commits == 1
    assert connection.executions[0]["statement"].startswith("merge dbo.model_run_log")
    assert "on target.run_id = source.run_id" in connection.executions[0]["statement"]
    assert connection.executions[0]["params"][0] == run_result.run_id
    assert connection.executions[1]["statement"].startswith("merge dbo.model_output_snapshot_metadata")


class _FakeBlobService:
    def __init__(self):
        self.uploads = []

    def get_blob_client(self, container: str, blob: str):
        return _FakeBlobClient(self.uploads, container, blob)


class _FakeBlobClient:
    def __init__(self, uploads, container: str, blob: str):
        self._uploads = uploads
        self._container = container
        self._blob = blob

    def upload_blob(self, handle, overwrite: bool):
        self._uploads.append(
            {
                "container": self._container,
                "blob": self._blob,
                "payload": handle.read(),
                "overwrite": overwrite,
            }
        )


class ServiceRequestError(Exception):
    pass


class _FlakyBlobService:
    def __init__(self):
        self.attempts = {}

    def get_blob_client(self, container: str, blob: str):
        return _FlakyBlobClient(self.attempts, container, blob)


class _FlakyBlobClient:
    def __init__(self, attempts, container: str, blob: str):
        self._attempts = attempts
        self._key = f"{container}/{blob.rsplit('/', 1)[-1]}"

    def upload_blob(self, handle, overwrite: bool):
        self._attempts[self._key] = self._attempts.get(self._key, 0) + 1
        if self._attempts[self._key] == 1:
            raise ServiceRequestError("temporary outage")
        handle.read()


class _FakeTracker:
    def __init__(self):
        self.tags = {}
        self.metrics = {}

    def set_tag(self, key, value):
        self.tags[key] = value

    def log_metric(self, key, value):
        self.metrics[key] = value


class _FlakyTracker(_FakeTracker):
    def __init__(self):
        super().__init__()
        self.failures = 0

    def set_tag(self, key, value):
        if self.failures == 0:
            self.failures += 1
            raise ServiceRequestError("temporary tracking outage")
        super().set_tag(key, value)


class _FlakyConnection:
    def __init__(self, connection):
        self._connection = connection
        self.failures = 0

    def execute(self, *args, **kwargs):
        statement = str(args[0]).strip().lower()
        if statement.startswith("insert") and self.failures == 0:
            self.failures += 1
            raise ServiceRequestError("temporary sql outage")
        return self._connection.execute(*args, **kwargs)

    def commit(self):
        return self._connection.commit()


class _RecordingConnection:
    def __init__(self):
        self.executions = []
        self.commits = 0

    def execute(self, statement, params):
        self.executions.append({"statement": statement, "params": params})

    def commit(self):
        self.commits += 1


def _create_sqlite_snapshot_table(connection) -> None:
    connection.execute(
        """
        create table model_output_snapshot_metadata (
            run_id text primary key,
            environment text,
            snapshot_uri text,
            row_count integer,
            drift_status text,
            output_schema_version text,
            created_at_utc text
        )
        """
    )


def _run_result(tmp_path) -> RunResult:
    run_id = "20260525T000000Z-test"
    run_dir = tmp_path / run_id
    run_dir.mkdir()
    for filename in (
        "curated_pricing.csv",
        "model_output_snapshot.csv",
        "model_drift_log.json",
        "model_run_log.json",
        "report.md",
    ):
        (run_dir / filename).write_text("x", encoding="utf-8")
    metadata = RunMetadata(
        run_id=run_id,
        status="succeeded",
        row_count=1,
        validation_status="passed",
        drift_status="green",
        started_at_utc="2026-05-25T00:00:00+00:00",
        finished_at_utc="2026-05-25T00:00:01+00:00",
        model_version="pricing-baseline-flow/0.1.0",
        logic_version="controlled-pricing-baseline-v1",
        environment="staging",
        owner="team46",
        trigger_type="manual",
        input_blob_path="samples/sample_pricing_v1.csv",
    )
    return RunResult(
        metadata=metadata,
        manifest=manifest_from_run_dir(run_dir, run_id),
        run_dir=run_dir,
    )
