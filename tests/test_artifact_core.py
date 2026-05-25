from __future__ import annotations

from pathlib import Path

from pricing_mlops.artifact_publishing import ArtifactPublisher, ComponentStateLayout, PublishStatus, RunMetadata, RunResult
from pricing_mlops.artifact_publishing.layout import ArtifactLayout, RunPartition, manifest_from_run_dir
from pricing_mlops.artifact_publishing.publishing import SinkPublishResult


def test_artifact_layout_preserves_existing_blob_partition_and_filenames(tmp_path):
    run_dir = _run_dir(tmp_path, "20260525T000000Z-test")
    manifest = manifest_from_run_dir(run_dir, "20260525T000000Z-test")
    layout = ArtifactLayout.default()

    targets = layout.blob_targets(
        manifest,
        RunPartition(
            environment="staging",
            compute_target="azure-ml",
            trigger_type="event-grid",
            owner="team46",
            run_id="20260525T000000Z-test",
        ),
    )

    assert targets["model_run_log"].container == "runs"
    assert targets["model_run_log"].blob_path == (
        "environment=staging/compute=azure-ml/trigger=event-grid/"
        "owner=team46/run_date=20260525/run_id=20260525T000000Z-test/model_run_log.json"
    )
    assert targets["curated_dataset"].container == "curated"
    assert targets["curated_artifact"].container == "artifacts"
    assert targets["curated_dataset"].blob_path.endswith("curated_pricing.csv")
    assert targets["model_output_snapshot"].blob_path.endswith("model_output_snapshot.csv")
    assert targets["model_drift_log"].blob_path.endswith("model_drift_log.json")
    assert targets["report"].blob_path.endswith("report.md")


def test_component_state_layout_centralizes_intermediate_pipeline_paths():
    layout = ComponentStateLayout()

    assert layout.prepared_prefix("20260525T000000Z-test") == "component-state/20260525T000000Z-test/prepared"
    assert layout.run_artifacts_prefix("20260525T000000Z-test") == (
        "component-state/20260525T000000Z-test/run_artifacts"
    )
    assert layout.prepared_filenames() == ("curated_input.csv", "validation_metadata.json")


def test_publisher_reports_partial_when_optional_sink_fails(tmp_path):
    run_result = _run_result(tmp_path)
    publisher = ArtifactPublisher(
        sinks=(
            _FakeSink("blob", required=True, result=SinkPublishResult("blob", PublishStatus.SUCCEEDED)),
            _FakeSink("sql", required=False, result=SinkPublishResult("sql", PublishStatus.FAILED)),
        )
    )

    result = publisher.publish(run_result)

    assert result.status == PublishStatus.PARTIAL
    assert not result.ok


def test_publisher_fails_when_required_sink_fails(tmp_path):
    run_result = _run_result(tmp_path)
    publisher = ArtifactPublisher(
        sinks=(
            _FakeSink("blob", required=True, result=SinkPublishResult("blob", PublishStatus.FAILED)),
            _FakeSink("sql", required=False, result=SinkPublishResult("sql", PublishStatus.SUCCEEDED)),
        )
    )

    result = publisher.publish(run_result)

    assert result.status == PublishStatus.FAILED


class _FakeSink:
    def __init__(self, name: str, required: bool, result: SinkPublishResult):
        self.name = name
        self.required = required
        self._result = result

    def publish(self, run_result: RunResult) -> SinkPublishResult:
        return self._result


def _run_dir(tmp_path: Path, run_id: str) -> Path:
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
    return run_dir


def _run_result(tmp_path: Path) -> RunResult:
    run_dir = _run_dir(tmp_path, "20260525T000000Z-test")
    metadata = RunMetadata(
        run_id="20260525T000000Z-test",
        status="succeeded",
        row_count=1,
        validation_status="passed",
        drift_status="green",
        started_at_utc="2026-05-25T00:00:00+00:00",
        finished_at_utc="2026-05-25T00:00:01+00:00",
        model_version="pricing-baseline-flow/0.1.0",
        logic_version="controlled-pricing-baseline-v1",
    )
    return RunResult(
        metadata=metadata,
        manifest=manifest_from_run_dir(run_dir, metadata.run_id),
        run_dir=run_dir,
    )
