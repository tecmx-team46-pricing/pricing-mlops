from pathlib import Path

from pricing.auth_monitoring import (
    expected_auth_monitoring_artifacts,
    load_auth_monitoring_config,
    validate_expected_monitoring_artifacts,
)


def test_auth_monitoring_config_is_versioned_and_typed():
    config = load_auth_monitoring_config()

    assert config.project.name == "pricing-mlops"
    assert config.project.monitoring_scope == "AUTH_ONLY"
    assert config.columns.key_columns == ("kpn", "vpareadescription", "distysegment")
    assert config.columns.official_recommendation_preferred == (
        "Selected_Optimal_Price",
        "selected_recommended_price",
    )
    assert config.thresholds.psi.yellow < config.thresholds.psi.red
    assert config.thresholds.current_history_coverage.red < config.thresholds.current_history_coverage.yellow
    assert config.schemas.recommendation_validity == "auth_recommendation_validity_v4_operational_decision"


def test_auth_monitoring_config_overrides_do_not_mutate_official_config():
    official_config = load_auth_monitoring_config()

    notebook_config = official_config.with_overrides(
        thresholds={
            "psi_yellow": 0.2,
            "psi_red": None,
            "scoring_update_new_combo_count_threshold": 25,
        }
    )

    assert official_config.thresholds.psi.yellow == 0.1
    assert official_config.thresholds.psi.red == 0.25
    assert official_config.thresholds.scoring_update_new_combo_count_threshold == 10
    assert notebook_config.thresholds.psi.yellow == 0.2
    assert notebook_config.thresholds.psi.red == 0.25
    assert notebook_config.thresholds.scoring_update_new_combo_count_threshold == 25


def test_auth_monitoring_config_rejects_unknown_overrides():
    config = load_auth_monitoring_config()

    try:
        config.with_overrides(thresholds={"psii_yellow": 0.2})
    except KeyError as exc:
        assert "psii_yellow" in str(exc)
    else:
        raise AssertionError("Unknown threshold override should fail fast")


def test_auth_monitoring_artifact_contract_is_local_and_publishable():
    artifacts = expected_auth_monitoring_artifacts()

    assert artifacts["operational_decision_summary"].relative_path == Path(
        "summaries/operational_decision_summary.csv"
    )
    assert artifacts["notification_payload"].relative_path == Path("summaries/notification_payload.json")
    assert artifacts["notification_payload"].platform_container_key == "runs"
    assert artifacts["simulated_operational_handoff"].relative_path == Path(
        "summaries/simulated_operational_handoff.json"
    )
    assert artifacts["simulated_operational_handoff"].platform_container_key == "runs"
    assert artifacts["simulated_operational_handoff_report"].relative_path == Path(
        "reports/simulated_operational_handoff.md"
    )
    assert artifacts["simulated_operational_handoff_report"].platform_container_key == "reports"
    assert artifacts["auth_history_drift_log"].relative_path == Path("logs/auth_history_drift_log.csv")
    assert artifacts["artifact_manifest"].relative_path == Path("manifest/artifact_manifest.json")
    assert all(not artifact.relative_path.is_absolute() for artifact in artifacts.values())
    assert all(artifact.platform_container_key for artifact in artifacts.values())


def test_auth_monitoring_artifact_contract_validates_expected_files(tmp_path):
    artifacts = expected_auth_monitoring_artifacts()
    for artifact in artifacts.values():
        if artifact.logical_name == "auth_history_drift_log":
            continue
        path = tmp_path / artifact.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")

    validation = validate_expected_monitoring_artifacts(tmp_path)

    assert not validation.is_complete
    assert [record["logical_name"] for record in validation.missing_required] == ["auth_history_drift_log"]
