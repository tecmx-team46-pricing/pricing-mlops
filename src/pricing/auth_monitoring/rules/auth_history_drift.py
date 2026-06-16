from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math

from pricing.auth_monitoring.values import to_float
from pricing.auth_monitoring.config import AuthMonitoringConfig, load_auth_monitoring_config
from pricing.types import Row


@dataclass(frozen=True)
class AuthHistoryDriftResult:
    drift_log: list[Row]


NUMERIC_HISTORY_VARIABLES = (
    "P20_PRICE",
    "P50_PRICE",
    "P85_PRICE",
    "P20",
    "P50",
    "P85",
    "revenue_sum",
    "quantity_sum",
    "n_transactions",
    "n_invoices",
    "log_quantity_mean",
    "log_into_stock_price_mean",
    "distributor_margin_pct_median",
    "channel_margin_share_median",
    "kemet_margin_pct_median",
    "negative_distributor_margin_rate",
    "negative_kemet_variable_margin_rate",
    "price_band_width",
)

CATEGORICAL_HISTORY_VARIABLES = (
    "vpareadescription",
    "distysegment",
    "custombusinessgroup_mode",
    "distributor_parentnumber_mode",
)

KS_HISTORY_VARIABLES = (
    "P50_PRICE",
    "revenue_sum",
    "quantity_sum",
    "distributor_margin_pct_median",
    "price_band_width",
)


def calculate_auth_history_drift(
    *,
    baseline_auth_history_profile: list[Row],
    current_auth_history: list[Row],
    run_id: str,
    config: AuthMonitoringConfig | None = None,
) -> AuthHistoryDriftResult:
    cfg = config or load_auth_monitoring_config()
    baseline_columns = set().union(*(row.keys() for row in baseline_auth_history_profile)) if baseline_auth_history_profile else set()
    current_columns = set().union(*(row.keys() for row in current_auth_history)) if current_auth_history else set()
    bin_columns = sorted(column for column in baseline_columns & current_columns if str(column).startswith("bin_"))

    numeric_vars = [column for column in NUMERIC_HISTORY_VARIABLES if column in baseline_columns and column in current_columns]
    categorical_vars = [
        column
        for column in (*CATEGORICAL_HISTORY_VARIABLES, *bin_columns)
        if column in baseline_columns and column in current_columns
    ]
    ks_vars = [column for column in KS_HISTORY_VARIABLES if column in baseline_columns and column in current_columns]

    drift_records: list[Row] = []
    for column in numeric_vars:
        psi = calculate_numeric_psi(_column_values(baseline_auth_history_profile, column), _column_values(current_auth_history, column))
        drift_records.append(
            _drift_record(
                run_id=run_id,
                variable_name=column,
                variable_type="numeric",
                drift_metric="PSI",
                drift_value=psi,
                p_value=float("nan"),
                yellow=cfg.thresholds.psi.yellow,
                red=cfg.thresholds.psi.red,
                monitoring_scope=cfg.project.monitoring_scope,
            )
        )
    for column in categorical_vars:
        psi = calculate_categorical_psi(_column_values(baseline_auth_history_profile, column), _column_values(current_auth_history, column))
        drift_records.append(
            _drift_record(
                run_id=run_id,
                variable_name=column,
                variable_type="categorical",
                drift_metric="Categorical_PSI",
                drift_value=psi,
                p_value=float("nan"),
                yellow=cfg.thresholds.psi.yellow,
                red=cfg.thresholds.psi.red,
                monitoring_scope=cfg.project.monitoring_scope,
            )
        )
    for column in ks_vars:
        ks_stat, p_value = calculate_ks_statistic(
            _column_values(baseline_auth_history_profile, column),
            _column_values(current_auth_history, column),
        )
        drift_records.append(
            _drift_record(
                run_id=run_id,
                variable_name=column,
                variable_type="numeric",
                drift_metric="KS",
                drift_value=ks_stat,
                p_value=p_value,
                yellow=cfg.thresholds.ks.yellow,
                red=cfg.thresholds.ks.red,
                monitoring_scope=cfg.project.monitoring_scope,
            )
        )
    return AuthHistoryDriftResult(drift_log=drift_records)


def _drift_record(
    *,
    run_id: str,
    variable_name: str,
    variable_type: str,
    drift_metric: str,
    drift_value: float,
    p_value: float,
    yellow: float,
    red: float,
    monitoring_scope: str,
) -> Row:
    status = classify_metric_status(drift_value, yellow, red)
    return {
        "drift_run_id": run_id,
        "monitoring_stage": "auth_history_pre_model",
        "variable_name": variable_name,
        "variable_type": variable_type,
        "drift_metric": drift_metric,
        "drift_value": drift_value,
        "p_value": p_value,
        "threshold_yellow": yellow,
        "threshold_red": red,
        "drift_status": status,
        "recommended_action": status_to_action(status),
        "monitoring_scope": monitoring_scope,
    }


def calculate_numeric_psi(expected: list[object], actual: list[object], bins: int = 10, epsilon: float = 1e-6) -> float:
    expected_values = sorted(_to_finite_float(value) for value in expected)
    actual_values = sorted(_to_finite_float(value) for value in actual)
    expected_values = [value for value in expected_values if value is not None]
    actual_values = [value for value in actual_values if value is not None]
    if not expected_values or not actual_values:
        return float("nan")
    if len(set(expected_values)) <= 1:
        return 0.0 if len(set(actual_values)) <= 1 else float("nan")
    breakpoints = _quantile_breakpoints(expected_values, bins)
    if len(breakpoints) < 3:
        return float("nan")
    expected_pct = _bin_percentages(expected_values, breakpoints, epsilon)
    actual_pct = _bin_percentages(actual_values, breakpoints, epsilon)
    return sum((actual - expected) * math.log(actual / expected) for expected, actual in zip(expected_pct, actual_pct))


def calculate_categorical_psi(expected: list[object], actual: list[object], epsilon: float = 1e-6) -> float:
    expected_values = [str(value if value not in (None, "") else "__MISSING__") for value in expected]
    actual_values = [str(value if value not in (None, "") else "__MISSING__") for value in actual]
    categories = sorted(set(expected_values) | set(actual_values))
    expected_counts = Counter(expected_values)
    actual_counts = Counter(actual_values)
    expected_total = sum(expected_counts.values()) or 1
    actual_total = sum(actual_counts.values()) or 1
    psi = 0.0
    for category in categories:
        expected_pct = expected_counts[category] / expected_total or epsilon
        actual_pct = actual_counts[category] / actual_total or epsilon
        psi += (actual_pct - expected_pct) * math.log(actual_pct / expected_pct)
    return psi


def calculate_ks_statistic(expected: list[object], actual: list[object]) -> tuple[float, float]:
    expected_values = _finite_numeric_values(expected)
    actual_values = _finite_numeric_values(actual)
    if not expected_values or not actual_values:
        return float("nan"), float("nan")
    values = sorted(set(expected_values) | set(actual_values))
    max_distance = 0.0
    expected_sorted = sorted(expected_values)
    actual_sorted = sorted(actual_values)
    for value in values:
        expected_cdf = _count_lte(expected_sorted, value) / len(expected_sorted)
        actual_cdf = _count_lte(actual_sorted, value) / len(actual_sorted)
        max_distance = max(max_distance, abs(expected_cdf - actual_cdf))
    return max_distance, float("nan")


def classify_metric_status(value: float, yellow_threshold: float, red_threshold: float, higher_is_worse: bool = True) -> str:
    if value != value:
        return "Not_Evaluable"
    if higher_is_worse:
        if value >= red_threshold:
            return "Red"
        if value >= yellow_threshold:
            return "Yellow"
        return "Green"
    if value <= red_threshold:
        return "Red"
    if value <= yellow_threshold:
        return "Yellow"
    return "Green"


def status_to_action(status: str, stage: str = "history") -> str:
    if status == "Green":
        return "No action / Continue monitoring"
    if status == "Yellow":
        return "Review with Pricing / PM"
    if status == "Red":
        if stage == "validity":
            return "Review recommendation; consider running model"
        return "Review history drift; consider model refresh or recalibration"
    return "Check data availability / metric not evaluable"


def _column_values(rows: list[Row], column: str) -> list[object]:
    return [row.get(column) for row in rows]


def _finite_numeric_values(values) -> list[float]:
    return [value for value in (_to_finite_float(raw_value) for raw_value in values) if value is not None]


def _to_finite_float(value: object) -> float | None:
    result = to_float(value)
    return None if result != result or math.isinf(result) else result


def _quantile_breakpoints(values: list[float], bins: int) -> list[float]:
    if not values:
        return []
    breakpoints = []
    for index in range(bins + 1):
        position = index * (len(values) - 1) / bins
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            breakpoints.append(values[int(position)])
        else:
            fraction = position - lower
            breakpoints.append(values[lower] * (1 - fraction) + values[upper] * fraction)
    return sorted(set(breakpoints))


def _bin_percentages(values: list[float], breakpoints: list[float], epsilon: float) -> list[float]:
    counts = [0 for _ in range(len(breakpoints) - 1)]
    for value in values:
        for index, (lower, upper) in enumerate(zip(breakpoints, breakpoints[1:])):
            if (index == 0 and lower <= value <= upper) or (index > 0 and lower < value <= upper):
                counts[index] += 1
                break
    total = sum(counts) or 1
    return [count / total or epsilon for count in counts]


def _count_lte(values: list[float], limit: float) -> int:
    return sum(1 for value in values if value <= limit)
