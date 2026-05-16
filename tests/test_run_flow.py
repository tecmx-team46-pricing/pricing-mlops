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
    assert (run_dir / "model_output_snapshot.csv").exists()
    assert (run_dir / "model_drift_log.json").exists()
    assert (run_dir / "report.md").exists()

    run_log = json.loads((run_dir / "model_run_log.json").read_text())
    assert run_log["status"] == "succeeded"
    assert run_log["row_count"] == 1
    assert run_log["run_id"] == result.run_id
