from scripts.components.build_baseline_snapshot import build_local_baseline_snapshot


def test_build_local_baseline_snapshot_writes_model_output_snapshot(tmp_path):
    feature_table = tmp_path / "feature_table.csv"
    output_dir = tmp_path / "outputs"
    feature_table.write_text(
        "kpn,vpareadescription,distysegment,Balanced,P20_PRICE,P50_PRICE,P85_PRICE\n"
        "KPN_1,VP_1,SEG_1,10,8,10,12\n",
        encoding="utf-8",
    )

    build_local_baseline_snapshot(feature_table_path=feature_table, output_dir=output_dir, run_id="baseline-run")

    assert (output_dir / "snapshots" / "model_output_snapshot.csv").exists()
