from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from pricing.auth_monitoring.values import is_nan, to_float
from pricing.auth_monitoring.config import AuthMonitoringConfig, load_auth_monitoring_config
from pricing.types import Row


@dataclass(frozen=True)
class RecommendationValidityResult:
    validity_log: list[Row]
    validity_summary: list[Row]
    validity_revenue_summary: list[Row]
    validity_reason_summary: list[Row]
    new_combo_log: list[Row]


def calculate_recommendation_validity(
    *,
    baseline_recommendation_snapshot: list[Row],
    baseline_auth_history_profile: list[Row],
    current_auth_history: list[Row],
    config: AuthMonitoringConfig | None = None,
) -> RecommendationValidityResult:
    cfg = config or load_auth_monitoring_config()
    key_columns = cfg.columns.key_columns
    baseline_history_by_key = {_key(row, key_columns): row for row in baseline_auth_history_profile}
    current_history_by_key = {_key(row, key_columns): row for row in current_auth_history}

    validity_log = [
        _classify_recommendation(
            recommendation=row,
            baseline_history=baseline_history_by_key.get(_key(row, key_columns), {}),
            current_history=current_history_by_key.get(_key(row, key_columns), {}),
            config=cfg,
        )
        for row in baseline_recommendation_snapshot
    ]
    new_combo_log = _new_combo_log(current_auth_history, baseline_recommendation_snapshot, cfg)
    return RecommendationValidityResult(
        validity_log=validity_log,
        validity_summary=_validity_summary(validity_log),
        validity_revenue_summary=_validity_revenue_summary(validity_log),
        validity_reason_summary=_validity_reason_summary(validity_log),
        new_combo_log=new_combo_log,
    )


def _classify_recommendation(
    *,
    recommendation: Row,
    baseline_history: Row,
    current_history: Row,
    config: AuthMonitoringConfig,
) -> Row:
    row: Row = dict(recommendation)
    key_columns = config.columns.key_columns
    row.update({f"baseline_{key}": value for key, value in baseline_history.items() if key not in key_columns})
    row.update({f"current_{key}": value for key, value in current_history.items() if key not in key_columns})

    baseline_price = to_float(row.get("baseline_recommended_price"))
    if is_nan(baseline_price):
        baseline_price = _first_numeric(row, config.columns.official_recommendation_preferred)
    row["baseline_recommended_price"] = baseline_price

    for prefix in ("baseline", "current"):
        _add_band_metrics(row, prefix, config)
    row["current_auth_band_is_valid"] = row["current_band_state"] == "Valid_Band"
    row["baseline_auth_band_is_valid"] = row["baseline_band_state"] == "Valid_Band"
    row["current_single_price_regime"] = row["current_band_state"] == "Collapsed_Band"

    row["recommendation_position_current_auth_band"] = _position(row, "current")
    row["recommendation_position_baseline_auth_band"] = _position(row, "baseline")
    row["recommendation_position_shift_current_vs_baseline"] = (
        _nan_subtract(row["recommendation_position_current_auth_band"], row["recommendation_position_baseline_auth_band"])
    )
    row["recommendation_gap_vs_current_auth_p50"] = _nan_subtract(baseline_price, to_float(row.get("current_P50_PRICE")))
    row["recommendation_gap_vs_current_auth_p50_pct"] = _safe_ratio(
        row["recommendation_gap_vs_current_auth_p50"], to_float(row.get("current_P50_PRICE"))
    )
    row["current_auth_p50_shift_vs_baseline_pct"] = _safe_ratio(
        _nan_subtract(to_float(row.get("current_P50_PRICE")), to_float(row.get("baseline_P50_PRICE"))),
        to_float(row.get("baseline_P50_PRICE")),
    )

    row["recommendation_below_current_auth_p20"] = (
        row["current_auth_band_is_valid"] and baseline_price < to_float(row.get("current_P20_PRICE"))
    )
    row["recommendation_above_current_auth_p85"] = (
        row["current_auth_band_is_valid"] and baseline_price > to_float(row.get("current_P85_PRICE"))
    )
    row["recommendation_outside_current_auth_band"] = (
        row["recommendation_below_current_auth_p20"] or row["recommendation_above_current_auth_p85"]
    )
    baseline_position = to_float(row.get("recommendation_position_baseline_auth_band"))
    row["recommendation_outside_baseline_auth_band"] = (
        row["baseline_auth_band_is_valid"] and (baseline_position < 0 or baseline_position > 1)
    )
    row["recommendation_near_current_auth_band_edge"] = _near_edge(row, "current", config)
    row["recommendation_near_baseline_auth_band_edge"] = _near_edge(row, "baseline", config)
    row["edge_transition_type"] = _classify_edge_transition(row)
    row["current_margin_floor_risk"] = (
        "current_Min_P20_for_5pct_margin" in row
        and baseline_price < to_float(row.get("current_Min_P20_for_5pct_margin"))
    )
    row["baseline_revenue_sum_numeric"] = to_float(row.get("baseline_revenue_sum"), 0.0)
    status, reason = _classify_with_config(row, config)
    row["auth_recommendation_validity_status"] = status
    row["auth_recommendation_validity_reason"] = reason
    row["alert_profile"] = config.thresholds.alert_profile
    row["recommended_action"] = _validity_action_map()[status]
    row["monitoring_stage"] = "recommendation_validity_pre_model"
    row["monitoring_scope"] = config.project.monitoring_scope
    row["runs_model"] = config.project.runs_model
    return row


def _add_band_metrics(row: Row, prefix: str, config: AuthMonitoringConfig) -> None:
    p20 = to_float(row.get(f"{prefix}_P20_PRICE"))
    p50 = to_float(row.get(f"{prefix}_P50_PRICE"))
    p85 = to_float(row.get(f"{prefix}_P85_PRICE"))
    has_history = not any(is_nan(value) for value in (p20, p50, p85))
    row[f"has_{prefix}_auth_history" if prefix == "current" else "has_baseline_auth_band"] = has_history
    width = p85 - p20 if has_history else float("nan")
    row[f"{prefix}_auth_band_width"] = width
    row[f"{prefix}_auth_band_width_pct"] = _safe_ratio(width, abs(p50))
    row[f"{prefix}_band_state"] = _classify_band_state(row, prefix, config)


def _classify_band_state(row: Row, prefix: str, config: AuthMonitoringConfig) -> str:
    has_history_key = "has_current_auth_history" if prefix == "current" else "has_baseline_auth_band"
    if not bool(row.get(has_history_key, False)):
        return "No_History"
    p20 = to_float(row.get(f"{prefix}_P20_PRICE"))
    p50 = to_float(row.get(f"{prefix}_P50_PRICE"))
    p85 = to_float(row.get(f"{prefix}_P85_PRICE"))
    width = to_float(row.get(f"{prefix}_auth_band_width"))
    width_pct = to_float(row.get(f"{prefix}_auth_band_width_pct"))
    n_tx = to_float(row.get(f"{prefix}_n_transactions"))
    if any(is_nan(value) for value in (p20, p50, p85)):
        return "Invalid_Band"
    if (p20 > p50 + 1e-12) or (p50 > p85 + 1e-12):
        return "Invalid_Band"
    if not is_nan(n_tx) and n_tx < config.thresholds.min_transactions_for_band:
        return "Low_Support_Band"
    if is_nan(width) or width <= 1e-12:
        return "Collapsed_Band"
    if not is_nan(width_pct) and width_pct < config.thresholds.min_band_width_pct:
        return "Collapsed_Band"
    return "Valid_Band"


def _classify_edge_transition(row: Row) -> str:
    if not bool(row.get("has_current_auth_history", False)):
        return "No_Current_History"
    curr_state = row.get("current_band_state")
    base_state = row.get("baseline_band_state")
    if curr_state == "Invalid_Band":
        return "Invalid_Current_Band"
    if curr_state == "Low_Support_Band":
        return "Low_Support_Current_Band"
    if curr_state == "Collapsed_Band":
        return "Single_Price_Regime"
    if curr_state != "Valid_Band":
        return str(curr_state)
    current_outside = bool(row.get("recommendation_outside_current_auth_band", False))
    baseline_outside = bool(row.get("recommendation_outside_baseline_auth_band", False))
    current_edge = bool(row.get("recommendation_near_current_auth_band_edge", False))
    baseline_edge = bool(row.get("recommendation_near_baseline_auth_band_edge", False))
    if current_outside and baseline_outside:
        return "Persistent_Outside"
    if current_outside and not baseline_outside:
        return "Moved_Outside"
    if current_edge and baseline_edge:
        return "Persistent_Edge"
    if current_edge and not baseline_edge:
        if base_state != "Valid_Band":
            return "Current_Edge_Baseline_Not_Evaluable"
        return "Moved_To_Edge"
    if (not current_edge) and baseline_edge:
        return "Moved_Away_From_Edge"
    return "Persistent_Interior"


def _classify_with_config(row: Row, config: AuthMonitoringConfig) -> tuple[str, str]:
    if not bool(row.get("has_current_auth_history", False)):
        return "Not_Evaluable", "No current AUTH history for this baseline recommendation"
    if bool(row.get("current_margin_floor_risk", False)):
        return "Red", "Recommendation below current margin floor"
    curr_state = row.get("current_band_state")
    gap_abs = abs(to_float(row.get("recommendation_gap_vs_current_auth_p50_pct")))
    shift_abs = abs(to_float(row.get("current_auth_p50_shift_vs_baseline_pct")))
    edge_transition = row.get("edge_transition_type")

    if curr_state == "Invalid_Band":
        return "Not_Evaluable", "Current AUTH band invalid; cannot evaluate recommendation position"
    if curr_state == "Collapsed_Band":
        if not is_nan(gap_abs) and gap_abs >= config.thresholds.collapsed_gap_red:
            return "Red", "Single-price regime; recommendation far from current AUTH P50"
        if not is_nan(gap_abs) and gap_abs >= config.thresholds.collapsed_gap_yellow:
            return "Yellow", "Single-price regime; recommendation moderately far from current AUTH P50"
        return "Watch", "Single-price regime / collapsed band; recommendation close to current AUTH P50"
    if curr_state == "Low_Support_Band":
        if not is_nan(gap_abs) and gap_abs >= config.thresholds.gap_vs_p50_red:
            return "Red", "Low-support current band; recommendation far from current AUTH P50"
        if not is_nan(gap_abs) and gap_abs >= config.thresholds.gap_vs_p50_yellow:
            return "Yellow", "Low-support current band; recommendation moderately far from current AUTH P50"
        return "Watch", "Low-support current band; monitor before treating edge as actionable"
    if bool(row.get("recommendation_below_current_auth_p20", False)):
        return "Red", "Recommendation below current AUTH P20"
    if bool(row.get("recommendation_above_current_auth_p85", False)):
        return "Red", "Recommendation above current AUTH P85"
    if not is_nan(gap_abs) and gap_abs >= config.thresholds.gap_vs_p50_red:
        return "Red", "Recommendation far from current AUTH P50"
    if edge_transition in ["Moved_To_Edge", "Current_Edge_Baseline_Not_Evaluable"]:
        return "Yellow", "Recommendation moved toward current AUTH band edge"
    if not is_nan(shift_abs) and shift_abs >= config.thresholds.p50_shift_red:
        return "Yellow", "Current AUTH P50 shifted strongly vs baseline; review before keeping recommendation"
    if not is_nan(gap_abs) and gap_abs >= config.thresholds.gap_vs_p50_yellow:
        return "Yellow", "Recommendation moderately far from current AUTH P50"
    if edge_transition == "Persistent_Edge":
        return "Watch", "Recommendation was already near band edge in baseline; monitor as persistent edge"
    if edge_transition == "Moved_Away_From_Edge":
        return "Watch", "Recommendation moved away from baseline edge; monitor"
    if not is_nan(shift_abs) and shift_abs >= config.thresholds.p50_shift_yellow:
        return "Watch", "Current AUTH P50 shifted moderately vs baseline"
    return "Green", "Recommendation aligned with current AUTH history"


def _new_combo_log(current_history: list[Row], baseline_snapshot: list[Row], config: AuthMonitoringConfig) -> list[Row]:
    key_columns = config.columns.key_columns
    baseline_keys = {_key(row, key_columns) for row in baseline_snapshot}
    return [
        {
            **{key: row.get(key, "") for key in key_columns},
            "coverage_status": "New_Combo_No_Baseline_Recommendation",
            "recommended_action": "Review coverage; generate recommendation when scoring/model run is approved",
        }
        for row in current_history
        if _key(row, key_columns) not in baseline_keys
    ]


def _validity_summary(rows: list[Row]) -> list[Row]:
    counts = Counter(str(row.get("auth_recommendation_validity_status", "Not_Evaluable")) for row in rows)
    total = len(rows) or 1
    return [
        {"auth_recommendation_validity_status": status, "n_recommendations": count, "share": count / total}
        for status, count in sorted(counts.items())
    ]


def _validity_revenue_summary(rows: list[Row]) -> list[Row]:
    total = sum(to_float(row.get("baseline_revenue_sum_numeric"), 0.0) for row in rows)
    sums: defaultdict[str, float] = defaultdict(float)
    for row in rows:
        sums[str(row.get("auth_recommendation_validity_status", "Not_Evaluable"))] += to_float(
            row.get("baseline_revenue_sum_numeric"), 0.0
        )
    return [
        {
            "auth_recommendation_validity_status": status,
            "baseline_revenue_sum": value,
            "baseline_revenue_share": value / total if total > 0 else float("nan"),
        }
        for status, value in sorted(sums.items())
    ]


def _validity_reason_summary(rows: list[Row]) -> list[Row]:
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    revenue_total = sum(to_float(row.get("baseline_revenue_sum_numeric"), 0.0) for row in rows)
    for row in rows:
        key = (
            str(row.get("auth_recommendation_validity_status", "Not_Evaluable")),
            str(row.get("auth_recommendation_validity_reason", "")),
        )
        item = grouped.setdefault(
            key,
            {
                "auth_recommendation_validity_status": key[0],
                "auth_recommendation_validity_reason": key[1],
                "n_recommendations": 0,
                "baseline_revenue_sum": 0.0,
            },
        )
        item["n_recommendations"] = int(item["n_recommendations"]) + 1
        item["baseline_revenue_sum"] = float(item["baseline_revenue_sum"]) + to_float(
            row.get("baseline_revenue_sum_numeric"), 0.0
        )
    total = len(rows) or 1
    result = []
    for item in grouped.values():
        revenue_sum = float(item["baseline_revenue_sum"])
        result.append(
            {
                **item,
                "share": int(item["n_recommendations"]) / total,
                "baseline_revenue_share": revenue_sum / revenue_total if revenue_total > 0 else float("nan"),
            }
        )
    return sorted(result, key=lambda row: (str(row["auth_recommendation_validity_status"]), -float(row["baseline_revenue_sum"])))


def _validity_action_map() -> dict[str, str]:
    return {
        "Green": "Keep current recommendation / no model run required",
        "Watch": "Keep with monitoring; not necessarily an immediate review case",
        "Yellow": "Review with Pricing / PM before keeping recommendation",
        "Red": "Run model or recalibrate/review before relying on recommendation",
        "Not_Evaluable": "Review coverage or band quality; recommendation cannot be evaluated cleanly",
    }


def _key(row: Row, columns: tuple[str, ...]) -> tuple[object, ...]:
    return tuple(row.get(column, "") for column in columns)


def _first_numeric(row: Row, columns: tuple[str, ...]) -> float:
    for column in columns:
        value = to_float(row.get(column))
        if not is_nan(value):
            return value
    return float("nan")


def _position(row: Row, prefix: str) -> float:
    flag = "current_auth_band_is_valid" if prefix == "current" else "baseline_auth_band_is_valid"
    if not bool(row.get(flag, False)):
        return float("nan")
    return _safe_ratio(
        _nan_subtract(to_float(row.get("baseline_recommended_price")), to_float(row.get(f"{prefix}_P20_PRICE"))),
        to_float(row.get(f"{prefix}_auth_band_width")),
    )


def _near_edge(row: Row, prefix: str, config: AuthMonitoringConfig) -> bool:
    flag = "current_auth_band_is_valid" if prefix == "current" else "baseline_auth_band_is_valid"
    if not bool(row.get(flag, False)):
        return False
    position = to_float(row.get(f"recommendation_position_{prefix}_auth_band"))
    return (
        not is_nan(position)
        and (
            0 <= position <= config.thresholds.near_band_edge_threshold
            or 1 - config.thresholds.near_band_edge_threshold <= position <= 1
        )
    )


def _safe_ratio(numerator: object, denominator: object) -> float:
    numerator_value = to_float(numerator)
    denominator_value = to_float(denominator)
    if is_nan(numerator_value) or is_nan(denominator_value) or abs(denominator_value) <= 1e-12:
        return float("nan")
    return numerator_value / denominator_value


def _nan_subtract(left: object, right: object) -> float:
    left_value = to_float(left)
    right_value = to_float(right)
    if is_nan(left_value) or is_nan(right_value):
        return float("nan")
    return left_value - right_value
