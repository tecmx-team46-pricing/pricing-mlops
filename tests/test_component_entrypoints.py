import json

from pricing_mlops.monitoring.pipeline.registry import get_monitoring_step, monitoring_step_slugs
from scripts.components.validate_prepare import prepare_local_input
from pricing.auth_monitoring import expected_auth_monitoring_artifacts, validate_expected_monitoring_artifacts
from pricing_mlops.monitoring.pipeline.steps.auth_history_drift_step import run_auth_history_drift_step
from pricing_mlops.monitoring.pipeline.steps.operational_decision_step import run_operational_decision_step
from pricing_mlops.monitoring.pipeline.steps.recommendation_validity_step import run_recommendation_validity_step


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


def test_monitoring_step_registry_defines_azureml_owned_steps():
    assert monitoring_step_slugs() == (
        "build_monitoring_inputs",
        "calculate_recommendation_validity",
        "calculate_auth_history_drift",
        "calculate_operational_decision",
    )

    definition = get_monitoring_step("calculate_operational_decision")

    assert definition.slug == "calculate_operational_decision"
    assert definition.component_name == "pricing_mlops_calculate_operational_decision"
    assert definition.input_dir == "outputs/auth_history_drift"
    assert definition.output_dir == "outputs/operational_decision"
    assert definition.state_container_arg == "validity_container"
    assert definition.state_prefix_arg == "validity_prefix"
    assert definition.publish_container_arg == "decision_container"
    assert definition.publish_prefix_arg == "decision_prefix"


def test_monitoring_components_write_step_artifacts(tmp_path):
    input_dir = tmp_path / "monitoring_inputs"
    validity_dir = tmp_path / "validity"
    drift_dir = tmp_path / "drift"
    decision_dir = tmp_path / "decision"
    snapshots_dir = input_dir / "snapshots"
    snapshots_dir.mkdir(parents=True)
    (snapshots_dir / "baseline_recommendation_snapshot.csv").write_text(
        "\n".join(
            [
                "kpn,vpareadescription,distysegment,baseline_recommended_price,baseline_revenue_sum",
                "KPN-001,North,Enterprise,20,1000",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    history_csv = "\n".join(
        [
            "kpn,vpareadescription,distysegment,P20_PRICE,P50_PRICE,P85_PRICE,n_transactions,revenue_sum",
            "KPN-001,North,Enterprise,8,10,12,20,1000",
        ]
    ) + "\n"
    (snapshots_dir / "baseline_auth_history_profile.csv").write_text(history_csv, encoding="utf-8")
    (snapshots_dir / "current_auth_history_snapshot_real.csv").write_text(history_csv, encoding="utf-8")

    run_recommendation_validity_step(input_dir=input_dir, output_dir=validity_dir)
    run_auth_history_drift_step(
        input_dir=validity_dir,
        output_dir=drift_dir,
        run_id="20260615T000000Z-auth-monitoring",
    )
    run_operational_decision_step(
        input_dir=drift_dir,
        output_dir=decision_dir,
        run_id="20260615T000000Z-auth-monitoring",
    )

    assert (validity_dir / "logs" / "auth_recommendation_validity_log.csv").is_file()
    assert (validity_dir / "summaries" / "validity_revenue_summary.csv").is_file()
    assert (drift_dir / "logs" / "auth_history_drift_log.csv").is_file()
    assert (decision_dir / "summaries" / "run_readiness_summary.csv").is_file()
    assert (decision_dir / "summaries" / "operational_decision_summary.csv").is_file()
    assert (decision_dir / "reports" / "auth_recommendation_validity_report.md").is_file()
    assert validate_expected_monitoring_artifacts(decision_dir).is_complete
    expected_paths = {
        artifact.relative_path.as_posix()
        for artifact in expected_auth_monitoring_artifacts().values()
    }
    expected_paths.remove("manifest/artifact_manifest.json")
    manifest = json.loads((decision_dir / "manifest" / "artifact_manifest.json").read_text())
    assert expected_paths.issubset({item["relative_path"] for item in manifest["artifacts"]})
