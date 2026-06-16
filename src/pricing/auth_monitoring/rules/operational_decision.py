from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from pricing.auth_monitoring.values import to_float
from pricing.auth_monitoring.config import AuthMonitoringConfig, load_auth_monitoring_config
from pricing.types import Row


@dataclass(frozen=True)
class OperationalDecisionResult:
    run_readiness_summary: Row
    operational_decision_summary: Row


def calculate_operational_decision(
    *,
    run_id: str,
    validity_log: list[Row],
    validity_revenue_summary: list[Row],
    new_combo_log: list[Row],
    data_quality_log: list[Row] | None = None,
    recommendation_coverage_log: list[Row] | None = None,
    catalog_bin_coverage_log: list[Row] | None = None,
    input_history_drift_log: list[Row] | None = None,
    config: AuthMonitoringConfig | None = None,
) -> OperationalDecisionResult:
    cfg = config or load_auth_monitoring_config()
    data_quality_log = data_quality_log or [{"check_status": "PASS"}]
    recommendation_coverage_log = recommendation_coverage_log or [{"check_status": "PASS"}]
    catalog_bin_coverage_log = catalog_bin_coverage_log or [{"coverage_status": "Green"}]
    input_history_drift_log = input_history_drift_log or [{"variable_name": "P50_PRICE", "drift_metric": "PSI", "drift_status": "Green"}]

    data_quality_status = aggregate_status(_map_quality_status(row.get("check_status")) for row in data_quality_log)
    recommendation_coverage_status = aggregate_status(row.get("check_status") for row in recommendation_coverage_log)
    catalog_bin_coverage_status = aggregate_status(row.get("coverage_status") for row in catalog_bin_coverage_log)
    history_drift_only = [row for row in input_history_drift_log if row.get("monitoring_stage") != "coverage_pre_model"]
    auth_history_drift_status = aggregate_status(row.get("drift_status") for row in history_drift_only)
    price_drift_log = [
        row
        for row in input_history_drift_log
        if row.get("variable_name") in {"P20_PRICE", "P50_PRICE", "P85_PRICE"}
        and row.get("drift_metric") in {"PSI", "KS"}
    ]
    price_drift_status = aggregate_status(row.get("drift_status") for row in price_drift_log) if price_drift_log else "Not_Evaluable"

    status_values = [str(row.get("auth_recommendation_validity_status", "Not_Evaluable")) for row in validity_log]
    denominator = len(status_values) or 1
    red_rate = status_values.count("Red") / denominator
    yellow_rate = status_values.count("Yellow") / denominator
    watch_rate = status_values.count("Watch") / denominator
    not_eval_rate = status_values.count("Not_Evaluable") / denominator
    red_revenue_share = _revenue_share_for_status(validity_revenue_summary, "Red")
    yellow_revenue_share = _revenue_share_for_status(validity_revenue_summary, "Yellow")
    watch_revenue_share = _revenue_share_for_status(validity_revenue_summary, "Watch")

    if (
        red_rate >= cfg.thresholds.global_validity_red_rate_threshold
        or red_revenue_share >= cfg.thresholds.global_validity_red_revenue_share_threshold
    ):
        recommendation_validity_global_status = "Red"
    elif (
        yellow_rate >= cfg.thresholds.global_validity_yellow_rate_threshold
        or yellow_revenue_share >= cfg.thresholds.global_validity_yellow_revenue_share_threshold
    ):
        recommendation_validity_global_status = "Yellow"
    elif (
        watch_rate >= cfg.thresholds.global_watch_rate_threshold
        or watch_revenue_share >= cfg.thresholds.global_watch_revenue_share_threshold
    ):
        recommendation_validity_global_status = "Watch"
    else:
        recommendation_validity_global_status = "Green"

    new_combo_rate = _new_combo_rate(new_combo_log, validity_log)
    scoring_update_needed = (
        new_combo_rate >= cfg.thresholds.scoring_update_new_combo_rate_threshold
        or len(new_combo_log) >= cfg.thresholds.scoring_update_new_combo_count_threshold
    )
    existing_recommendation_material_risk = (
        red_revenue_share >= cfg.thresholds.actionable_red_revenue_share_for_retrain_review
        or recommendation_validity_global_status == "Red"
    )
    price_drift_material = price_drift_status == "Red"
    catalog_review_needed = catalog_bin_coverage_status == "Red"

    if data_quality_status == "Red":
        recommended_operational_action = "FIX_DATA_QUALITY_BEFORE_DECISION"
        scoring_update_recommendation = "HOLD"
        hb_svi_retraining_recommendation = "NOT_EVALUABLE_UNTIL_DATA_QUALITY_FIXED"
        run_readiness_status = "Red"
        run_readiness_decision = "Do not rely on monitoring result; fix structural data quality first."
    elif existing_recommendation_material_risk and price_drift_material:
        recommended_operational_action = "REVIEW_AND_EVALUATE_HB_SVI_RETRAINING"
        scoring_update_recommendation = "RUN_FULL_RECOMMENDATION_REFRESH_AFTER_REVIEW"
        hb_svi_retraining_recommendation = "RETRAINING_CANDIDATE_PRICE_DRIFT_AND_RECOMMENDATION_RISK"
        run_readiness_status = "Red"
        run_readiness_decision = "Existing recommendations and price drift show material risk; evaluate HB-SVI retraining and full recommendation refresh."
    elif existing_recommendation_material_risk:
        recommended_operational_action = "REVIEW_RED_YELLOW_CASES_AND_RUN_RECOMMENDATION_REFRESH"
        scoring_update_recommendation = "RUN_RECOMMENDATION_REFRESH_FOR_EXISTING_AND_NEW_COMBOS"
        hb_svi_retraining_recommendation = "NOT_REQUIRED_FROM_PRICE_DRIFT_ALONE"
        run_readiness_status = "Red"
        run_readiness_decision = "Existing recommendations have material actionable risk, but HB-SVI retraining requires separate model-health/price-drift evidence."
    elif scoring_update_needed and price_drift_status in ["Green", "Yellow", "Watch", "Not_Evaluable"]:
        recommended_operational_action = "RUN_SCORING_UPDATE_FOR_NEW_COMBOS"
        scoring_update_recommendation = "RUN_SCORING_UPDATE_WITH_ELASTICITY_FALLBACK_POLICY"
        hb_svi_retraining_recommendation = "NOT_REQUIRED_FROM_PRICE_DRIFT_ALONE"
        run_readiness_status = "Yellow"
        run_readiness_decision = "New AUTH combos require recommendation coverage. Run scoring/update using existing, inherited, or default elasticity; full HB-SVI retraining is not required from price drift alone."
    elif catalog_review_needed:
        recommended_operational_action = "REVIEW_CATALOG_BIN_FALLBACK"
        scoring_update_recommendation = "RUN_AFTER_CATALOG_REVIEW_IF_NEEDED"
        hb_svi_retraining_recommendation = "NOT_REQUIRED_CATALOG_ISSUE"
        run_readiness_status = "Yellow"
        run_readiness_decision = "Catalog/bin coverage has material issues; review catalog/fallback logic before interpreting bin drift as business drift."
    elif auth_history_drift_status == "Red":
        recommended_operational_action = "REVIEW_HISTORY_DRIFT_WITH_PRICING_PM"
        scoring_update_recommendation = "CONDITIONAL"
        hb_svi_retraining_recommendation = "EVALUATE_IF_PRICE_OR_MODEL_HEALTH_DRIFT_IS_CONFIRMED"
        run_readiness_status = "Yellow"
        run_readiness_decision = "History changed materially; review with Pricing/PM before keeping recommendations or running model."
    elif (
        recommendation_validity_global_status == "Yellow"
        or recommendation_coverage_status == "Yellow"
        or auth_history_drift_status == "Yellow"
        or data_quality_status == "Yellow"
        or catalog_bin_coverage_status == "Yellow"
    ):
        recommended_operational_action = "REVIEW_ACTIONABLE_YELLOW_CASES"
        scoring_update_recommendation = "OPTIONAL_BASED_ON_BUSINESS_CAPACITY"
        hb_svi_retraining_recommendation = "NOT_REQUIRED_FROM_CURRENT_MONITORING"
        run_readiness_status = "Yellow"
        run_readiness_decision = "Review selected actionable segments/cases; scoring update may be needed depending on business impact."
    elif recommendation_validity_global_status == "Watch":
        recommended_operational_action = "KEEP_WITH_WATCH_MONITORING"
        scoring_update_recommendation = "NOT_REQUIRED_FOR_EXISTING_RECOMMENDATIONS"
        hb_svi_retraining_recommendation = "NOT_REQUIRED"
        run_readiness_status = "Watch"
        run_readiness_decision = "Keep recommendations with monitoring; most signals are watchlist rather than actionable review."
    else:
        recommended_operational_action = "KEEP_CURRENT_RECOMMENDATIONS"
        scoring_update_recommendation = "NOT_REQUIRED"
        hb_svi_retraining_recommendation = "NOT_REQUIRED"
        run_readiness_status = "Green"
        run_readiness_decision = "Current recommendations remain aligned with current AUTH history; no model run required."

    if catalog_bin_coverage_status == "Red":
        catalog_rebaseline_recommendation = "REVIEW_CATALOG_FALLBACK_OR_CATALOG_V2"
    elif catalog_bin_coverage_status == "Yellow":
        catalog_rebaseline_recommendation = "WATCH_CATALOG_COVERAGE"
    else:
        catalog_rebaseline_recommendation = "KEEP_CURRENT_CATALOG_VERSION"

    run_readiness_summary: Row = {
        "drift_run_id": run_id,
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "monitoring_scope": cfg.project.monitoring_scope,
        "current_history_interpretation": cfg.project.current_history_interpretation,
        "runs_model": cfg.project.runs_model,
        "alert_profile": cfg.thresholds.alert_profile,
        "bin_catalog_scope": cfg.project.bin_catalog_scope,
        "bin_catalog_version": cfg.project.bin_catalog_version,
        "baseline_recommendation_rows": len(validity_log),
        "new_combo_count": len(new_combo_log),
        "new_combo_rate": new_combo_rate,
        "data_quality_status": data_quality_status,
        "recommendation_coverage_status": recommendation_coverage_status,
        "catalog_bin_coverage_status": catalog_bin_coverage_status,
        "auth_history_drift_status": auth_history_drift_status,
        "price_drift_status": price_drift_status,
        "recommendation_validity_global_status": recommendation_validity_global_status,
        "run_readiness_status": run_readiness_status,
        "recommended_operational_action": recommended_operational_action,
        "scoring_update_recommendation": scoring_update_recommendation,
        "hb_svi_retraining_recommendation": hb_svi_retraining_recommendation,
        "catalog_rebaseline_recommendation": catalog_rebaseline_recommendation,
        "run_readiness_decision": run_readiness_decision,
        "green_recommendation_rate": status_values.count("Green") / denominator,
        "watch_recommendation_rate": watch_rate,
        "yellow_recommendation_rate": yellow_rate,
        "red_recommendation_rate": red_rate,
        "not_evaluable_recommendation_rate": not_eval_rate,
        "green_revenue_share": _revenue_share_for_status(validity_revenue_summary, "Green"),
        "watch_revenue_share": watch_revenue_share,
        "yellow_revenue_share": yellow_revenue_share,
        "red_revenue_share": red_revenue_share,
        "not_evaluable_revenue_share": _revenue_share_for_status(validity_revenue_summary, "Not_Evaluable"),
        "min_band_width_pct": cfg.thresholds.min_band_width_pct,
        "min_transactions_for_band": cfg.thresholds.min_transactions_for_band,
    }
    operational_decision_summary: Row = {
        "drift_run_id": run_id,
        "recommended_operational_action": recommended_operational_action,
        "scoring_update_recommendation": scoring_update_recommendation,
        "hb_svi_retraining_recommendation": hb_svi_retraining_recommendation,
        "catalog_rebaseline_recommendation": catalog_rebaseline_recommendation,
        "decision_rationale": run_readiness_decision,
        "price_drift_status": price_drift_status,
        "recommendation_validity_global_status": recommendation_validity_global_status,
        "recommendation_coverage_status": recommendation_coverage_status,
        "catalog_bin_coverage_status": catalog_bin_coverage_status,
        "auth_history_drift_status": auth_history_drift_status,
    }
    return OperationalDecisionResult(run_readiness_summary, operational_decision_summary)


def aggregate_status(statuses) -> str:
    normalized = {str(status) for status in statuses if status not in (None, "")}
    if "FAIL" in normalized or "Red" in normalized:
        return "Red"
    if "WARNING" in normalized or "Yellow" in normalized:
        return "Yellow"
    if "Watch" in normalized:
        return "Watch"
    if "PASS" in normalized or "Green" in normalized:
        return "Green"
    return "Not_Evaluable"


def _map_quality_status(status: object) -> str:
    return {"FAIL": "Red", "WARNING": "Yellow", "PASS": "Green"}.get(str(status), str(status))


def _revenue_share_for_status(rows: list[Row], status: str) -> float:
    return sum(to_float(row.get("baseline_revenue_share"), 0.0) for row in rows if row.get("auth_recommendation_validity_status") == status)


def _new_combo_rate(new_combo_log: list[Row], validity_log: list[Row]) -> float:
    denominator = len(new_combo_log) + len(validity_log)
    return len(new_combo_log) / denominator if denominator else 0.0
