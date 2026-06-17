from pricing.auth_monitoring.rules.auth_history_drift import (
    calculate_auth_history_drift,
    calculate_categorical_psi,
    calculate_numeric_psi,
)
from pricing.auth_monitoring.rules.operational_decision import calculate_operational_decision
from pricing.auth_monitoring.rules.recommendation_validity import calculate_recommendation_validity
from pricing_mlops.monitoring.pipeline.steps.simulate_operational_handoff_step import (
    build_simulated_operational_handoff,
)


def test_recommendation_validity_preserves_notebook_red_band_logic():
    result = calculate_recommendation_validity(
        baseline_recommendation_snapshot=[
            _recommendation("KPN-001", 10.0, revenue=1000),
            _recommendation("KPN-002", 20.0, revenue=500),
        ],
        baseline_auth_history_profile=[
            _history("KPN-001", 8.0, 10.0, 12.0, revenue=1000),
            _history("KPN-002", 8.0, 10.0, 12.0, revenue=500),
        ],
        current_auth_history=[
            _history("KPN-001", 8.0, 10.0, 12.0, revenue=1000),
            _history("KPN-002", 8.0, 10.0, 12.0, revenue=500),
            _history("KPN-003", 4.0, 5.0, 6.0, revenue=100),
        ],
    )

    statuses = {
        row["kpn"]: row["auth_recommendation_validity_status"]
        for row in result.validity_log
    }

    assert statuses == {"KPN-001": "Green", "KPN-002": "Red"}
    assert result.validity_log[1]["auth_recommendation_validity_reason"] == "Recommendation above current AUTH P85"
    assert result.new_combo_log[0]["kpn"] == "KPN-003"


def test_operational_decision_preserves_material_recommendation_risk_path():
    validity = calculate_recommendation_validity(
        baseline_recommendation_snapshot=[_recommendation("KPN-001", 20.0, revenue=1000)],
        baseline_auth_history_profile=[_history("KPN-001", 8.0, 10.0, 12.0, revenue=1000)],
        current_auth_history=[_history("KPN-001", 8.0, 10.0, 12.0, revenue=1000)],
    )

    result = calculate_operational_decision(
        run_id="20260615T000000Z-auth-monitoring",
        validity_log=validity.validity_log,
        validity_revenue_summary=validity.validity_revenue_summary,
        new_combo_log=validity.new_combo_log,
        input_history_drift_log=[
            {"variable_name": "P50_PRICE", "drift_metric": "PSI", "drift_status": "Green"}
        ],
    )

    assert result.run_readiness_summary["run_readiness_status"] == "Red"
    assert (
        result.operational_decision_summary["recommended_operational_action"]
        == "REVIEW_RED_YELLOW_CASES_AND_RUN_RECOMMENDATION_REFRESH"
    )
    assert (
        result.operational_decision_summary["hb_svi_retraining_recommendation"]
        == "NOT_REQUIRED_FROM_PRICE_DRIFT_ALONE"
    )
    assert "notification_severity" not in result.operational_decision_summary
    assert "should_notify" not in result.operational_decision_summary
    assert "blocking_decision" not in result.operational_decision_summary


def test_operational_decision_keeps_yellow_summary_free_of_notification_fields():
    validity = calculate_recommendation_validity(
        baseline_recommendation_snapshot=[_recommendation("KPN-001", 10.0, revenue=1000)],
        baseline_auth_history_profile=[_history("KPN-001", 8.0, 10.0, 12.0, revenue=1000)],
        current_auth_history=[
            _history("KPN-001", 8.0, 10.0, 12.0, revenue=1000),
            _history("KPN-002", 4.0, 5.0, 6.0, revenue=100),
        ],
    )

    result = calculate_operational_decision(
        run_id="20260615T000000Z-auth-monitoring",
        validity_log=validity.validity_log,
        validity_revenue_summary=validity.validity_revenue_summary,
        new_combo_log=validity.new_combo_log,
        input_history_drift_log=[
            {"variable_name": "P50_PRICE", "drift_metric": "PSI", "drift_status": "Green"}
        ],
    )

    assert result.run_readiness_summary["run_readiness_status"] == "Yellow"
    assert "notification_severity" not in result.operational_decision_summary
    assert "should_notify" not in result.operational_decision_summary
    assert "blocking_decision" not in result.operational_decision_summary


def test_operational_decision_keeps_green_summary_free_of_notification_fields():
    validity = calculate_recommendation_validity(
        baseline_recommendation_snapshot=[_recommendation("KPN-001", 10.0, revenue=1000)],
        baseline_auth_history_profile=[_history("KPN-001", 8.0, 10.0, 12.0, revenue=1000)],
        current_auth_history=[_history("KPN-001", 8.0, 10.0, 12.0, revenue=1000)],
    )

    result = calculate_operational_decision(
        run_id="20260615T000000Z-auth-monitoring",
        validity_log=validity.validity_log,
        validity_revenue_summary=validity.validity_revenue_summary,
        new_combo_log=validity.new_combo_log,
        input_history_drift_log=[
            {"variable_name": "P50_PRICE", "drift_metric": "PSI", "drift_status": "Green"}
        ],
    )

    assert result.run_readiness_summary["run_readiness_status"] == "Green"
    assert "notification_severity" not in result.operational_decision_summary
    assert "should_notify" not in result.operational_decision_summary
    assert "blocking_decision" not in result.operational_decision_summary


def test_auth_history_drift_writes_price_drift_signals():
    result = calculate_auth_history_drift(
        baseline_auth_history_profile=[
            _history("KPN-001", 8.0, 10.0, 12.0, revenue=1000),
            _history("KPN-002", 8.0, 10.0, 12.0, revenue=500),
        ],
        current_auth_history=[
            _history("KPN-001", 9.0, 11.0, 13.0, revenue=1000),
            _history("KPN-002", 10.0, 12.0, 14.0, revenue=500),
        ],
        run_id="20260615T000000Z-auth-monitoring",
    )

    metrics = {(row["variable_name"], row["drift_metric"]) for row in result.drift_log}

    assert ("P50_PRICE", "PSI") in metrics
    assert ("P50_PRICE", "KS") in metrics


def test_drift_utility_functions_keep_notebook_names():
    assert calculate_numeric_psi([10, 20, 30, 40], [10, 20, 30, 80]) > 0
    assert calculate_categorical_psi(["A", "A", "B"], ["A", "B", "B"]) > 0


def test_simulated_operational_handoff_maps_green_to_monitoring_only():
    payload = build_simulated_operational_handoff(
        run_readiness_summary={"run_readiness_status": "Green"},
        operational_decision_summary={
            "drift_run_id": "20260615T000000Z-auth-monitoring",
            "recommended_operational_action": "KEEP_CURRENT_RECOMMENDATIONS",
        },
    )

    assert payload == {
        "run_id": "20260615T000000Z-auth-monitoring",
        "run_readiness_status": "Green",
        "recommended_operational_action": "KEEP_CURRENT_RECOMMENDATIONS",
        "simulated_decision": "KEEP_CURRENT_RECOMMENDATIONS",
        "simulated_notification": False,
        "simulated_channel": "pricing-ops",
        "simulated_owner": "Pricing PM",
        "simulated_secondary_owner": "",
        "simulated_message": "Green monitoring result keeps current pricing recommendations with routine monitoring.",
        "placeholder_only": True,
    }


def test_simulated_operational_handoff_maps_watch_to_watch_monitoring():
    payload = build_simulated_operational_handoff(
        run_readiness_summary={"run_readiness_status": "Watch"},
        operational_decision_summary={
            "drift_run_id": "20260615T000000Z-auth-monitoring",
            "recommended_operational_action": "KEEP_WITH_WATCH_MONITORING",
        },
    )

    assert payload["simulated_decision"] == "KEEP_WITH_WATCH_MONITORING"
    assert payload["simulated_notification"] is False
    assert payload["simulated_owner"] == "Pricing PM"
    assert payload["simulated_secondary_owner"] == ""


def test_simulated_operational_handoff_maps_yellow_to_pricing_pm_review():
    payload = build_simulated_operational_handoff(
        run_readiness_summary={"run_readiness_status": "Yellow"},
        operational_decision_summary={
            "drift_run_id": "20260615T000000Z-auth-monitoring",
            "recommended_operational_action": "REVIEW_ACTIONABLE_YELLOW_CASES",
        },
    )

    assert payload["simulated_decision"] == "REVIEW_ACTIONABLE_CASES"
    assert payload["simulated_notification"] is True
    assert payload["simulated_owner"] == "Pricing PM"
    assert payload["simulated_secondary_owner"] == ""


def test_simulated_operational_handoff_maps_red_to_pause_or_review():
    payload = build_simulated_operational_handoff(
        run_readiness_summary={"run_readiness_status": "Red"},
        operational_decision_summary={
            "drift_run_id": "20260615T000000Z-auth-monitoring",
            "recommended_operational_action": "REVIEW_RED_YELLOW_CASES_AND_RUN_RECOMMENDATION_REFRESH",
        },
    )

    assert payload["simulated_decision"] == "PAUSE_OR_REVIEW_BEFORE_PUBLICATION"
    assert payload["simulated_notification"] is True
    assert payload["simulated_owner"] == "Pricing PM"
    assert payload["simulated_secondary_owner"] == "ML Owner"


def _recommendation(kpn, price, revenue):
    return {
        "kpn": kpn,
        "vpareadescription": "North",
        "distysegment": "Enterprise",
        "baseline_recommended_price": price,
        "baseline_revenue_sum": revenue,
    }


def _history(kpn, p20, p50, p85, revenue):
    return {
        "kpn": kpn,
        "vpareadescription": "North",
        "distysegment": "Enterprise",
        "P20_PRICE": p20,
        "P50_PRICE": p50,
        "P85_PRICE": p85,
        "n_transactions": 20,
        "revenue_sum": revenue,
    }
