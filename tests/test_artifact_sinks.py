from __future__ import annotations

import sqlite3

from pricing_mlops.artifacts import (
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
from pricing_mlops.artifacts.layout import manifest_from_run_dir


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


def test_azure_ml_sink_records_metadata_and_artifact_references(tmp_path):
    run_result = _run_result(tmp_path)
    tracker = _FakeTracker()

    result = AzureMlArtifactSink(tracking_client=tracker).publish(run_result)

    assert result.status == PublishStatus.SUCCEEDED
    assert tracker.tags["run_id"] == run_result.run_id
    assert tracker.metrics["row_count"] == 1
    assert tracker.tags["artifact.model_run_log"] == "model_run_log.json"


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
            publish_status text
        )
        """
    )
    sink = SqlRunMetadataSink(connection=connection)

    first = sink.publish(run_result)
    second = sink.publish(run_result)

    assert first.status == PublishStatus.SUCCEEDED
    assert second.status == PublishStatus.SUCCEEDED
    count = connection.execute("select count(*) from pricing_run_metadata").fetchone()[0]
    assert count == 1
    row = connection.execute("select run_id, environment, row_count from pricing_run_metadata").fetchone()
    assert row == (run_result.run_id, "staging", 1)


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


class _FakeTracker:
    def __init__(self):
        self.tags = {}
        self.metrics = {}

    def set_tag(self, key, value):
        self.tags[key] = value

    def log_metric(self, key, value):
        self.metrics[key] = value


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
