from pathlib import Path
from unittest.mock import Mock
import json

from scripts.upload_run_outputs import build_upload_plan, upload_run_outputs


def test_build_upload_plan_maps_artifacts_to_contract_containers(tmp_path):
    run_dir = tmp_path / "run-001"
    run_dir.mkdir()
    for name in [
        "model_output_snapshot.csv",
        "model_drift_log.json",
        "report.md",
        "curated_pricing.csv",
    ]:
        (run_dir / name).write_text("x")
    (run_dir / "model_run_log.json").write_text(json.dumps({"run_id": "run-001"}))

    plan = build_upload_plan(run_dir, environment="staging", run_owner="team46")

    assert plan["runs"].blob_path.startswith("environment=staging/owner=team46/")
    assert plan["curated"].container == "curated"
    assert plan["curated"].blob_path.startswith("environment=staging/owner=team46/")
    assert plan["curated"].blob_path.endswith("curated_pricing.csv")
    assert plan["runs"].blob_path.endswith("model_run_log.json")
    assert plan["snapshots"].blob_path.endswith("model_output_snapshot.csv")
    assert plan["drift-logs"].blob_path.endswith("model_drift_log.json")
    assert plan["reports"].blob_path.endswith("report.md")
    assert plan["artifacts"].blob_path.endswith("curated_pricing.csv")


def test_upload_run_outputs_uses_azure_cli_login_auth(tmp_path):
    run_dir = tmp_path / "20260516T000000Z-test"
    run_dir.mkdir()
    for name in [
        "model_output_snapshot.csv",
        "model_drift_log.json",
        "report.md",
        "curated_pricing.csv",
    ]:
        (run_dir / name).write_text("x")
    (run_dir / "model_run_log.json").write_text(
        json.dumps({"run_id": "20260516T000000Z-test"})
    )

    runner = Mock()

    upload_run_outputs(
        run_dir=run_dir,
        storage_account="stexample",
        environment="staging",
        run_owner="team46",
        containers={
            "runs": "runs",
            "curated": "curated",
            "snapshots": "snapshots",
            "drift_logs": "drift-logs",
            "reports": "reports",
            "artifacts": "artifacts",
        },
        runner=runner,
    )

    assert runner.call_count == 6
    first_command = runner.call_args_list[0].args[0]
    assert first_command[:4] == ["az", "storage", "blob", "upload"]
    assert "--auth-mode" in first_command
    assert "login" in first_command
    assert "--account-name" in first_command
    assert "stexample" in first_command
    assert any("owner=team46" in part for part in first_command)


def test_build_upload_plan_can_partition_by_compute_target(tmp_path):
    run_dir = tmp_path / "run-002"
    run_dir.mkdir()
    for name in [
        "model_output_snapshot.csv",
        "model_drift_log.json",
        "report.md",
        "curated_pricing.csv",
    ]:
        (run_dir / name).write_text("x")
    (run_dir / "model_run_log.json").write_text(json.dumps({"run_id": "run-002"}))

    plan = build_upload_plan(
        run_dir,
        environment="staging",
        run_owner="team46",
        compute_target="azure-ml",
    )

    assert plan["runs"].blob_path.startswith(
        "environment=staging/compute=azure-ml/owner=team46/"
    )


def test_build_upload_plan_can_partition_by_trigger_type(tmp_path):
    run_dir = tmp_path / "run-003"
    run_dir.mkdir()
    for name in [
        "model_output_snapshot.csv",
        "model_drift_log.json",
        "report.md",
        "curated_pricing.csv",
    ]:
        (run_dir / name).write_text("x")
    (run_dir / "model_run_log.json").write_text(json.dumps({"run_id": "run-003"}))

    plan = build_upload_plan(
        run_dir,
        environment="staging",
        run_owner="team46",
        compute_target="azure-ml",
        trigger_type="event-grid",
    )

    assert plan["runs"].blob_path.startswith(
        "environment=staging/compute=azure-ml/trigger=event-grid/owner=team46/"
    )
