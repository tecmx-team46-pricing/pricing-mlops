from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pricing_mlops.monitoring.pipeline.steps.auth_history_drift_step import run_auth_history_drift_step
from pricing_mlops.monitoring.pipeline.steps.build_monitoring_inputs import build_monitoring_inputs
from pricing_mlops.monitoring.pipeline.steps.operational_decision_step import run_operational_decision_step
from pricing_mlops.monitoring.pipeline.steps.recommendation_validity_step import run_recommendation_validity_step


StepRunner = Callable[..., Any]
SummaryBuilder = Callable[[Any], dict[str, Any]]


@dataclass(frozen=True)
class MonitoringStepDefinition:
    slug: str
    component_name: str
    runner: StepRunner
    summary: SummaryBuilder
    input_dir: str = ""
    output_dir: str = ""
    baseline_snapshot_path: str = ""
    current_history_path: str = ""
    state_container_arg: str = ""
    state_prefix_arg: str = ""
    publish_container_arg: str = ""
    publish_prefix_arg: str = ""
    requires_run_id: bool = False

    @property
    def uses_snapshot_inputs(self) -> bool:
        return bool(self.baseline_snapshot_path and self.current_history_path)


MONITORING_STEPS: tuple[MonitoringStepDefinition, ...] = (
    MonitoringStepDefinition(
        slug="build_monitoring_inputs",
        component_name="pricing_mlops_build_monitoring_inputs",
        runner=build_monitoring_inputs,
        summary=lambda result: {
            "output_dir": str(result.output_dir),
            "recommendation_price_column": result.recommendation_price_column,
            "row_counts": result.row_counts,
        },
        output_dir="outputs/monitoring_inputs",
        baseline_snapshot_path="outputs/_downloaded/baseline_recommendation_snapshot.csv",
        current_history_path="outputs/_downloaded/current_auth_history_snapshot_real.csv",
        publish_container_arg="monitoring_inputs_container",
        publish_prefix_arg="monitoring_inputs_prefix",
        requires_run_id=True,
    ),
    MonitoringStepDefinition(
        slug="calculate_recommendation_validity",
        component_name="pricing_mlops_calculate_recommendation_validity",
        runner=run_recommendation_validity_step,
        summary=lambda result: {
            "validity_rows": len(result.validity_log),
            "new_combo_rows": len(result.new_combo_log),
            "summary_rows": len(result.validity_summary),
        },
        input_dir="outputs/monitoring_inputs",
        output_dir="outputs/recommendation_validity",
        state_container_arg="monitoring_inputs_container",
        state_prefix_arg="monitoring_inputs_prefix",
        publish_container_arg="validity_container",
        publish_prefix_arg="validity_prefix",
    ),
    MonitoringStepDefinition(
        slug="calculate_auth_history_drift",
        component_name="pricing_mlops_calculate_auth_history_drift",
        runner=run_auth_history_drift_step,
        summary=lambda result: {"drift_rows": len(result.drift_log)},
        input_dir="outputs/recommendation_validity",
        output_dir="outputs/auth_history_drift",
        state_container_arg="validity_container",
        state_prefix_arg="validity_prefix",
        publish_container_arg="drift_container",
        publish_prefix_arg="drift_prefix",
        requires_run_id=True,
    ),
    MonitoringStepDefinition(
        slug="calculate_operational_decision",
        component_name="pricing_mlops_calculate_operational_decision",
        runner=run_operational_decision_step,
        summary=lambda result: {
            "run_readiness_status": result.run_readiness_summary["run_readiness_status"],
            "recommended_operational_action": result.operational_decision_summary[
                "recommended_operational_action"
            ],
        },
        input_dir="outputs/auth_history_drift",
        output_dir="outputs/operational_decision",
        state_container_arg="validity_container",
        state_prefix_arg="validity_prefix",
        publish_container_arg="decision_container",
        publish_prefix_arg="decision_prefix",
        requires_run_id=True,
    ),
)


def monitoring_step_slugs() -> tuple[str, ...]:
    return tuple(step.slug for step in MONITORING_STEPS)


def get_monitoring_step(slug: str) -> MonitoringStepDefinition:
    for step in MONITORING_STEPS:
        if step.slug == slug:
            return step
    valid = ", ".join(monitoring_step_slugs())
    raise KeyError(f"unknown monitoring step: {slug}; expected one of: {valid}")


def run_registered_step(
    definition: MonitoringStepDefinition,
    *,
    input_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    run_id: str = "",
    baseline_snapshot_path: str | Path | None = None,
    current_history_path: str | Path | None = None,
) -> Any:
    if definition.uses_snapshot_inputs:
        return definition.runner(
            baseline_snapshot_path=baseline_snapshot_path or definition.baseline_snapshot_path,
            current_history_path=current_history_path or definition.current_history_path,
            output_dir=output_dir or definition.output_dir,
            run_id=run_id,
        )
    kwargs: dict[str, Any] = {
        "input_dir": input_dir or definition.input_dir,
        "output_dir": output_dir or definition.output_dir,
    }
    if definition.requires_run_id:
        kwargs["run_id"] = run_id
    return definition.runner(**kwargs)
