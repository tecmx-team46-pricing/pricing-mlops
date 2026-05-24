import json

from pricing_mlops.run import run_local_flow


def test_local_flow_writes_expected_artifacts(tmp_path):
    input_path = tmp_path / "sample.csv"
    output_root = tmp_path / "runs"
    input_path.write_text(
        "\n".join(
            [
                "kpn,vpareadescription,distysegment,current_price,P0_PRICE,P20_PRICE,P50_PRICE,P85_PRICE,P100_PRICE",
                "KPN-001,north,enterprise,10.0,8.0,9.0,10.0,11.0,13.0",
            ]
        )
        + "\n"
    )

    result = run_local_flow(input_path=input_path, output_root=output_root)

    run_dir = output_root / result.run_id
    assert run_dir.exists()
    assert (run_dir / "model_run_log.json").exists()
    assert (run_dir / "curated_pricing.csv").exists()
    assert (run_dir / "model_output_snapshot.csv").exists()
    assert (run_dir / "model_drift_log.json").exists()
    assert (run_dir / "report.md").exists()

    run_log = json.loads((run_dir / "model_run_log.json").read_text())
    assert run_log["status"] == "succeeded"
    assert run_log["row_count"] == 1
    assert run_log["run_id"] == result.run_id
    assert run_log["started_at_utc"]
    assert run_log["finished_at_utc"]
    assert run_log["output_path"] == str(run_dir)
    assert run_log["dataset_version"] == "local-sample"
    assert run_log["schema_version"] == "pricing_input_schema_v1"
    assert run_log["model_version"] == "pricing-baseline-flow/0.1.0"
    assert run_log["logic_version"] == "controlled-pricing-baseline-v1"
    assert run_log["config_version"] == "pricing_rules_config_v1"
    assert "git_commit_hash" in run_log
    assert run_log["artifacts"]["curated_dataset"] == "curated_pricing.csv"

    drift_log = json.loads((run_dir / "model_drift_log.json").read_text())
    assert drift_log["status"] in {"green", "yellow", "red"}
    assert drift_log["metrics"]
    assert {
        "variable",
        "metric",
        "value",
        "threshold_warning",
        "threshold_critical",
        "status",
    }.issubset(drift_log["metrics"][0])

    snapshot = (run_dir / "model_output_snapshot.csv").read_text()
    assert "floor_price" in snapshot
    assert "recommended_price" in snapshot
    assert "target_price" in snapshot

    report = (run_dir / "report.md").read_text()
    assert "Decision" in report
    assert result.run_id in report


def test_local_flow_accepts_external_run_id(tmp_path):
    input_path = tmp_path / "sample.csv"
    output_root = tmp_path / "runs"
    input_path.write_text(
        "\n".join(
            [
                "kpn,vpareadescription,distysegment,current_price,P0_PRICE,P20_PRICE,P50_PRICE,P85_PRICE,P100_PRICE",
                "KPN-001,north,enterprise,10.0,8.0,9.0,10.0,11.0,13.0",
            ]
        )
        + "\n"
    )

    result = run_local_flow(
        input_path=input_path,
        output_root=output_root,
        run_id="20260516T000000Z-gha-1",
    )

    assert result.run_id == "20260516T000000Z-gha-1"
    assert (output_root / "20260516T000000Z-gha-1" / "model_run_log.json").exists()
