import json

from scripts.components.publish_outputs import publish_component_outputs
from scripts.components.score_evaluate import run_component as run_score_evaluate
from scripts.components.validate_prepare import prepare_local_input


SAMPLE_CSV = "\n".join(
    [
        "kpn,vpareadescription,distysegment,current_price,P0_PRICE,P20_PRICE,P50_PRICE,P85_PRICE,P100_PRICE",
        "KPN-001,north,enterprise,10.0,8.0,9.0,10.0,11.0,13.0",
    ]
) + "\n"


def test_validate_prepare_writes_curated_input_and_metadata(tmp_path):
    input_path = tmp_path / "input.csv"
    prepared_dir = tmp_path / "prepared"
    input_path.write_text(SAMPLE_CSV)

    prepare_local_input(
        input_path=input_path,
        output_dir=prepared_dir,
        input_blob_path="incoming/pricing.csv",
    )

    metadata = json.loads((prepared_dir / "validation_metadata.json").read_text())
    curated = (prepared_dir / "curated_input.csv").read_text()

    assert metadata["input_blob_path"] == "incoming/pricing.csv"
    assert metadata["row_count"] == 1
    assert metadata["validation_status"] == "passed"
    assert "current_price" in curated


def test_score_evaluate_writes_run_artifacts_with_metadata(tmp_path):
    prepared_dir = tmp_path / "prepared"
    output_dir = tmp_path / "artifacts"
    prepared_dir.mkdir()
    (prepared_dir / "curated_input.csv").write_text(SAMPLE_CSV)
    (prepared_dir / "validation_metadata.json").write_text(
        json.dumps({"row_count": 1, "validation_status": "passed"})
    )

    run_score_evaluate(
        prepared_dir=prepared_dir,
        output_dir=output_dir,
        environment="staging",
        run_owner="team46",
        run_id="20260524T000000Z-event-grid",
        input_blob_path="incoming/pricing.csv",
        trigger_type="event-grid",
        model_repo="tecmx-team46-pricing/pricing-mlops",
        model_ref="PoC/model-flow-template",
        model_commit_sha="abc123",
    )

    expected_files = {
        "curated_pricing.csv",
        "model_output_snapshot.csv",
        "model_drift_log.json",
        "model_run_log.json",
        "report.md",
    }
    assert expected_files == {path.name for path in output_dir.iterdir()}

    run_log = json.loads((output_dir / "model_run_log.json").read_text())
    assert run_log["trigger_type"] == "event-grid"
    assert run_log["model_repo"] == "tecmx-team46-pricing/pricing-mlops"
    assert run_log["model_ref"] == "PoC/model-flow-template"
    assert run_log["model_commit_sha"] == "abc123"
    assert run_log["input_blob_path"] == "incoming/pricing.csv"


def test_publish_outputs_uses_trigger_partition(monkeypatch, tmp_path):
    run_dir = tmp_path / "artifacts"
    run_dir.mkdir()
    for name in [
        "model_output_snapshot.csv",
        "model_drift_log.json",
        "report.md",
        "curated_pricing.csv",
    ]:
        (run_dir / name).write_text("x")
    (run_dir / "model_run_log.json").write_text(
        json.dumps({"run_id": "20260524T000000Z-event-grid"})
    )
    uploads = []

    class FakeBlob:
        def __init__(self, container, blob):
            self.container = container
            self.blob = blob

        def upload_blob(self, handle, overwrite):
            uploads.append((self.container, self.blob, handle.read(), overwrite))

    class FakeBlobServiceClient:
        def __init__(self, account_url, credential):
            self.account_url = account_url
            self.credential = credential

        def get_blob_client(self, container, blob):
            return FakeBlob(container, blob)

    monkeypatch.setattr(
        "azure.storage.blob.BlobServiceClient",
        FakeBlobServiceClient,
    )
    monkeypatch.setattr(
        "scripts.components.publish_outputs.build_azure_credential",
        lambda: object(),
    )

    uploaded = publish_component_outputs(
        run_dir=run_dir,
        storage_account="<mlops-storage-account>",
        environment="staging",
        run_owner="team46",
        compute_target="azure-ml",
        trigger_type="event-grid",
        containers={
            "curated": "curated",
            "runs": "runs",
            "snapshots": "snapshots",
            "drift_logs": "drift-logs",
            "reports": "reports",
            "artifacts": "artifacts",
        },
    )

    assert uploaded["runs"].startswith(
        "environment=staging/compute=azure-ml/trigger=event-grid/owner=team46/"
    )
    assert len(uploads) == 6
