from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
import json
from pathlib import Path
from typing import Any, Mapping


DEFAULT_CONFIG_PATH = Path(__file__).with_name("auth_monitoring_config.json")


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    team: str
    environment: str
    monitoring_scope: str
    current_history_interpretation: str
    bin_catalog_scope: str
    bin_catalog_version: str
    runs_model: bool
    baseline_version: str


@dataclass(frozen=True)
class SchemasConfig:
    recommendation_validity: str
    input_history_drift: str
    data_quality: str


@dataclass(frozen=True)
class ColumnsConfig:
    key_columns: tuple[str, ...]
    official_recommendation_preferred: tuple[str, ...]
    proxy_recommendation: tuple[str, ...]
    baseline_history: tuple[str, ...]
    global_bin: tuple[str, ...]


@dataclass(frozen=True)
class AlertThreshold:
    yellow: float
    red: float

    def with_overrides(self, *, yellow: float | None = None, red: float | None = None) -> AlertThreshold:
        return replace(
            self,
            yellow=self.yellow if yellow is None else float(yellow),
            red=self.red if red is None else float(red),
        )


@dataclass(frozen=True)
class CoverageThreshold:
    yellow: float
    red: float

    def with_overrides(self, *, yellow: float | None = None, red: float | None = None) -> CoverageThreshold:
        return replace(
            self,
            yellow=self.yellow if yellow is None else float(yellow),
            red=self.red if red is None else float(red),
        )


@dataclass(frozen=True)
class ThresholdsConfig:
    alert_profile: str
    psi: AlertThreshold
    ks: AlertThreshold
    current_history_coverage: CoverageThreshold
    new_combo_rate: AlertThreshold
    min_segment_support_for_dashboard: int
    min_transactions_for_band: int = 5
    min_band_width_pct: float = 0.02
    near_band_edge_threshold: float = 0.1
    gap_vs_p50_yellow: float = 0.1
    gap_vs_p50_red: float = 0.25
    p50_shift_yellow: float = 0.1
    p50_shift_red: float = 0.25
    collapsed_gap_yellow: float = 0.05
    collapsed_gap_red: float = 0.15
    global_validity_red_rate_threshold: float = 0.05
    global_validity_yellow_rate_threshold: float = 0.15
    global_watch_rate_threshold: float = 0.3
    global_validity_red_revenue_share_threshold: float = 0.05
    global_validity_yellow_revenue_share_threshold: float = 0.15
    global_watch_revenue_share_threshold: float = 0.3
    scoring_update_new_combo_rate_threshold: float = 0.05
    scoring_update_new_combo_count_threshold: int = 10
    actionable_red_revenue_share_for_retrain_review: float = 0.05

    def with_overrides(self, overrides: Mapping[str, object | None] | None = None) -> ThresholdsConfig:
        if not overrides:
            return self

        unused = set(overrides)
        psi = self.psi.with_overrides(
            yellow=_take_float_override(overrides, unused, "psi_yellow"),
            red=_take_float_override(overrides, unused, "psi_red"),
        )
        ks = self.ks.with_overrides(
            yellow=_take_float_override(overrides, unused, "ks_yellow"),
            red=_take_float_override(overrides, unused, "ks_red"),
        )
        current_history_coverage = self.current_history_coverage.with_overrides(
            yellow=_take_float_override(overrides, unused, "current_history_coverage_yellow"),
            red=_take_float_override(overrides, unused, "current_history_coverage_red"),
        )
        new_combo_rate = self.new_combo_rate.with_overrides(
            yellow=_take_float_override(overrides, unused, "new_combo_rate_yellow"),
            red=_take_float_override(overrides, unused, "new_combo_rate_red"),
        )

        replacements: dict[str, object] = {
            "psi": psi,
            "ks": ks,
            "current_history_coverage": current_history_coverage,
            "new_combo_rate": new_combo_rate,
        }
        float_fields = {
            "min_band_width_pct",
            "near_band_edge_threshold",
            "gap_vs_p50_yellow",
            "gap_vs_p50_red",
            "p50_shift_yellow",
            "p50_shift_red",
            "collapsed_gap_yellow",
            "collapsed_gap_red",
            "global_validity_red_rate_threshold",
            "global_validity_yellow_rate_threshold",
            "global_watch_rate_threshold",
            "global_validity_red_revenue_share_threshold",
            "global_validity_yellow_revenue_share_threshold",
            "global_watch_revenue_share_threshold",
            "scoring_update_new_combo_rate_threshold",
            "actionable_red_revenue_share_for_retrain_review",
        }
        int_fields = {
            "min_segment_support_for_dashboard",
            "min_transactions_for_band",
            "scoring_update_new_combo_count_threshold",
        }

        for field_name in float_fields:
            value = _take_float_override(overrides, unused, field_name)
            if value is not None:
                replacements[field_name] = value
        for field_name in int_fields:
            value = _take_int_override(overrides, unused, field_name)
            if value is not None:
                replacements[field_name] = value

        if unused:
            raise KeyError(f"Unknown monitoring threshold override(s): {sorted(unused)}")

        return replace(self, **replacements)


@dataclass(frozen=True)
class AuthMonitoringConfig:
    project: ProjectConfig
    schemas: SchemasConfig
    columns: ColumnsConfig
    thresholds: ThresholdsConfig

    def with_overrides(
        self,
        *,
        thresholds: Mapping[str, object | None] | None = None,
    ) -> AuthMonitoringConfig:
        """Return a notebook/runtime copy with experimental overrides applied."""
        return replace(self, thresholds=self.thresholds.with_overrides(thresholds))


def load_auth_monitoring_config(path: str | Path | None = None) -> AuthMonitoringConfig:
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return _config_from_mapping(raw)


def _config_from_mapping(raw: Mapping[str, Any]) -> AuthMonitoringConfig:
    return AuthMonitoringConfig(
        project=ProjectConfig(**raw["project"]),
        schemas=SchemasConfig(**raw["schemas"]),
        columns=ColumnsConfig(
            key_columns=tuple(raw["columns"]["key_columns"]),
            official_recommendation_preferred=tuple(raw["columns"]["official_recommendation_preferred"]),
            proxy_recommendation=tuple(raw["columns"]["proxy_recommendation"]),
            baseline_history=tuple(raw["columns"]["baseline_history"]),
            global_bin=tuple(raw["columns"]["global_bin"]),
        ),
        thresholds=ThresholdsConfig(
            alert_profile=str(raw["thresholds"]["alert_profile"]),
            psi=AlertThreshold(**raw["thresholds"]["psi"]),
            ks=AlertThreshold(**raw["thresholds"]["ks"]),
            current_history_coverage=CoverageThreshold(**raw["thresholds"]["current_history_coverage"]),
            new_combo_rate=AlertThreshold(**raw["thresholds"]["new_combo_rate"]),
            min_segment_support_for_dashboard=int(raw["thresholds"]["min_segment_support_for_dashboard"]),
            min_transactions_for_band=int(raw["thresholds"].get("min_transactions_for_band", 5)),
            min_band_width_pct=float(raw["thresholds"].get("min_band_width_pct", 0.02)),
            near_band_edge_threshold=float(raw["thresholds"].get("near_band_edge_threshold", 0.1)),
            gap_vs_p50_yellow=float(raw["thresholds"].get("gap_vs_p50_yellow", 0.1)),
            gap_vs_p50_red=float(raw["thresholds"].get("gap_vs_p50_red", 0.25)),
            p50_shift_yellow=float(raw["thresholds"].get("p50_shift_yellow", 0.1)),
            p50_shift_red=float(raw["thresholds"].get("p50_shift_red", 0.25)),
            collapsed_gap_yellow=float(raw["thresholds"].get("collapsed_gap_yellow", 0.05)),
            collapsed_gap_red=float(raw["thresholds"].get("collapsed_gap_red", 0.15)),
            global_validity_red_rate_threshold=float(
                raw["thresholds"].get("global_validity_red_rate_threshold", 0.05)
            ),
            global_validity_yellow_rate_threshold=float(
                raw["thresholds"].get("global_validity_yellow_rate_threshold", 0.15)
            ),
            global_watch_rate_threshold=float(raw["thresholds"].get("global_watch_rate_threshold", 0.3)),
            global_validity_red_revenue_share_threshold=float(
                raw["thresholds"].get("global_validity_red_revenue_share_threshold", 0.05)
            ),
            global_validity_yellow_revenue_share_threshold=float(
                raw["thresholds"].get("global_validity_yellow_revenue_share_threshold", 0.15)
            ),
            global_watch_revenue_share_threshold=float(
                raw["thresholds"].get("global_watch_revenue_share_threshold", 0.3)
            ),
            scoring_update_new_combo_rate_threshold=float(
                raw["thresholds"].get("scoring_update_new_combo_rate_threshold", 0.05)
            ),
            scoring_update_new_combo_count_threshold=int(
                raw["thresholds"].get("scoring_update_new_combo_count_threshold", 10)
            ),
            actionable_red_revenue_share_for_retrain_review=float(
                raw["thresholds"].get("actionable_red_revenue_share_for_retrain_review", 0.05)
            ),
        ),
    )


def _take_float_override(
    overrides: Mapping[str, object | None],
    unused: set[str],
    key: str,
) -> float | None:
    if key not in overrides:
        return None
    unused.discard(key)
    value = overrides[key]
    return None if value is None else float(value)


def _take_int_override(
    overrides: Mapping[str, object | None],
    unused: set[str],
    key: str,
) -> int | None:
    if key not in overrides:
        return None
    unused.discard(key)
    value = overrides[key]
    return None if value is None else int(value)
