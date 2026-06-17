from pathlib import Path

from scripts.components.prepare_current_auth_history import prepare_local_current_history


def test_prepare_local_current_history_writes_snapshot(tmp_path):
    input_path = tmp_path / "curated_input.csv"
    output_dir = tmp_path / "outputs"
    input_path.write_text(
        "kpn,vpareadescription,distysegment,P20_PRICE,P50_PRICE,P85_PRICE,quantity,revenue_sum\n"
        "KPN_1,VP_1,SEG_1,8,10,12,2,20\n",
        encoding="utf-8",
    )

    prepare_local_current_history(input_path=input_path, output_dir=output_dir, run_id="run-1")

    assert (output_dir / "snapshots" / "current_auth_history_snapshot_real.csv").exists()
