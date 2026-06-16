import csv
import json

from pricing_mlops.monitoring.pipeline.steps.build_monitoring_inputs import build_monitoring_inputs


def test_build_monitoring_inputs_materializes_snapshot_contract(tmp_path):
    baseline_path = tmp_path / "model_output_snapshot.csv"
    current_path = tmp_path / "current_auth_history_snapshot_real.csv"
    output_dir = tmp_path / "outputs"
    _write_csv(
        baseline_path,
        [
            {
                "kpn": "KPN-001",
                "vpareadescription": "North",
                "distysegment": "Enterprise",
                "Selected_Optimal_Price": "10.5",
                "P20_PRICE": "8.0",
                "P50_PRICE": "10.0",
                "P85_PRICE": "12.0",
                "n_transactions": "20",
            }
        ],
    )
    _write_csv(
        current_path,
        [
            {
                "kpn": "KPN-001",
                "vpareadescription": "North",
                "distysegment": "Enterprise",
                "P20_PRICE": "8.5",
                "P50_PRICE": "10.3",
                "P85_PRICE": "12.4",
                "n_transactions": "25",
            }
        ],
    )

    result = build_monitoring_inputs(
        baseline_snapshot_path=baseline_path,
        current_history_path=current_path,
        output_dir=output_dir,
        run_id="20260615T000000Z-auth-monitoring",
    )

    assert result.recommendation_price_column == "Selected_Optimal_Price"
    assert result.row_counts == {
        "baseline_recommendations": 1,
        "baseline_auth_history": 1,
        "current_auth_history": 1,
    }
    assert (output_dir / "snapshots" / "baseline_recommendation_snapshot.csv").is_file()
    assert (output_dir / "snapshots" / "baseline_auth_history_profile.csv").is_file()
    assert (output_dir / "snapshots" / "current_auth_history_snapshot_real.csv").is_file()
    manifest = json.loads((output_dir / "manifest" / "artifact_manifest.json").read_text())
    assert {
        "baseline_recommendation_snapshot",
        "baseline_auth_history_profile",
        "current_auth_history_snapshot_real",
    }.issubset({item["logical_name"] for item in manifest["artifacts"]})


def _write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
