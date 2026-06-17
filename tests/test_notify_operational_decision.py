import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTIFY_COMPONENT = ROOT / "scripts" / "components" / "notify_operational_decision.py"


def _load_notify_component():
    spec = importlib.util.spec_from_file_location("notify_operational_decision", NOTIFY_COMPONENT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_validate_published_notification_payload_writes_smoke_summary(tmp_path, monkeypatch):
    module = _load_notify_component()

    def fake_download_blob(storage_account, container, blob_path, destination):
        assert storage_account == "stpmlops06152240"
        assert container == "runs"
        assert blob_path.endswith("/summaries/notification_payload.json")
        destination.write_text(
            json.dumps(
                {
                    "schema_version": "auth_monitoring_notification_v1",
                    "run_id": "20260616T000000Z-test",
                    "severity": "critical",
                    "should_notify": True,
                    "blocking_decision": True,
                    "title": "Pricing AUTH monitoring: Red decision",
                    "status": "Red",
                    "recommended_operational_action": "REVIEW_RED_YELLOW_CASES_AND_RUN_RECOMMENDATION_REFRESH",
                    "primary_reason": "Existing recommendations have material actionable risk.",
                    "next_action_owner": "Pricing PM",
                    "decision_rationale": "Existing recommendations have material actionable risk.",
                    "signals": {"recommendation_validity_global_status": "Red"},
                }
            ),
            encoding="utf-8",
        )

    monkeypatch.setattr(module, "download_blob", fake_download_blob)

    summary = module.validate_published_notification_payload(
        storage_account="stpmlops06152240",
        environment="staging",
        run_owner="team46",
        run_id="20260616T000000Z-test",
        trigger_type="batch-endpoint",
        output_dir=tmp_path,
    )

    assert summary["schema_version"] == "auth_monitoring_notification_smoke_v1"
    assert summary["severity"] == "critical"
    assert summary["should_notify"] is True
    assert summary["blocking_decision"] is True
    assert summary["payload_blob"].endswith("/summaries/notification_payload.json")
    assert json.loads((tmp_path / "notification_smoke_summary.json").read_text()) == summary
