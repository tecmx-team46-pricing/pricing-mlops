from __future__ import annotations

import json
from pathlib import Path

from pricing.auth_monitoring.artifact_contract import validate_expected_monitoring_artifacts
from pricing.types import Row
from pricing_mlops.io.artifacts import write_artifact_manifest
from pricing_mlops.io.csv import read_csv_rows
from pricing_mlops.io.filesystem import copy_tree


def run_simulate_operational_handoff_step(
    *,
    input_dir: str | Path,
    output_dir: str | Path,
    run_id: str,
) -> Row:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    copy_tree(input_dir, output_dir)
    run_readiness_summary = _single_summary_row(input_dir / "summaries" / "run_readiness_summary.csv")
    operational_decision_summary = _single_summary_row(
        input_dir / "summaries" / "operational_decision_summary.csv"
    )
    payload = build_simulated_operational_handoff(
        run_readiness_summary=run_readiness_summary,
        operational_decision_summary=operational_decision_summary,
    )
    if payload["run_id"] != run_id:
        raise ValueError(f"simulated handoff run_id mismatch: {payload['run_id']} != {run_id}")
    _write_json(output_dir / "summaries" / "simulated_operational_handoff.json", payload)
    _write_markdown_report(output_dir / "reports" / "simulated_operational_handoff.md", payload)
    write_artifact_manifest(output_dir, run_id)
    _validate_output_contract(output_dir)
    return payload


def build_simulated_operational_handoff(
    *,
    run_readiness_summary: Row,
    operational_decision_summary: Row,
) -> Row:
    status = str(run_readiness_summary.get("run_readiness_status") or "Not_Evaluable")
    action = str(operational_decision_summary.get("recommended_operational_action") or "REVIEW_REQUIRED")
    run_id = str(operational_decision_summary.get("drift_run_id") or "")
    decision = _simulated_decision(status)
    return {
        "run_id": run_id,
        "run_readiness_status": status,
        "recommended_operational_action": action,
        "simulated_decision": decision,
        "simulated_notification": status in {"Yellow", "Red", "Not_Evaluable"},
        "simulated_channel": "pricing-ops",
        "simulated_owner": "Pricing PM",
        "simulated_secondary_owner": "ML Owner" if status == "Red" else "",
        "simulated_message": _simulated_message(status),
        "placeholder_only": True,
    }


def _single_summary_row(path: Path) -> Row:
    rows = read_csv_rows(path)
    if len(rows) != 1:
        raise ValueError(f"expected exactly one row in {path}; found {len(rows)}")
    return rows[0]


def _simulated_decision(status: str) -> str:
    return {
        "Green": "KEEP_CURRENT_RECOMMENDATIONS",
        "Watch": "KEEP_WITH_WATCH_MONITORING",
        "Yellow": "REVIEW_ACTIONABLE_CASES",
        "Red": "PAUSE_OR_REVIEW_BEFORE_PUBLICATION",
    }.get(status, "REVIEW_REQUIRED")


def _simulated_message(status: str) -> str:
    return {
        "Green": "Green monitoring result keeps current pricing recommendations with routine monitoring.",
        "Watch": "Watch monitoring result is recorded for continued observation without escalation.",
        "Yellow": "Yellow monitoring result simulates a Pricing PM review of actionable cases.",
        "Red": "Red monitoring result requires review before publishing pricing recommendations.",
    }.get(status, "Monitoring result is not evaluable and requires manual review.")


def _write_json(path: Path, payload: Row) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_markdown_report(path: Path, payload: Row) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Simulated Operational Handoff",
                "",
                f"- Run ID: {payload['run_id']}",
                f"- Semaforo: {payload['run_readiness_status']}",
                f"- Simulated decision: {payload['simulated_decision']}",
                f"- Simulated notification: {payload['simulated_notification']}",
                f"- Owner: {payload['simulated_owner']}",
                f"- Secondary owner: {payload['simulated_secondary_owner']}",
                "",
                "This is a placeholder node. No external notification was sent.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _validate_output_contract(output_dir: Path) -> None:
    validation = validate_expected_monitoring_artifacts(output_dir)
    if validation.is_complete:
        return
    missing = ", ".join(str(record["relative_path"]) for record in validation.missing_required)
    raise FileNotFoundError(f"AUTH monitoring output contract is incomplete; missing: {missing}")
