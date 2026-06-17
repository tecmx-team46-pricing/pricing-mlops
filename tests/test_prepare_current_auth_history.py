from pathlib import Path

from pricing_mlops.monitoring.pipeline.steps.prepare_current_auth_history import (
    prepare_current_auth_history,
)


def write_csv(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def test_prepare_current_auth_history_aggregates_by_monitoring_key(tmp_path):
    input_path = tmp_path / "curated_input.csv"
    output_dir = tmp_path / "out"
    write_csv(
        input_path,
        """
kpn,vpareadescription,distysegment,current_price,quantity,revenue_sum,P20_PRICE,P50_PRICE,P85_PRICE
KPN_1,VP_1,SEG_1,10,2,20,8,10,12
KPN_1,VP_1,SEG_1,14,1,14,8,10,12
KPN_2,VP_1,SEG_1,5,3,15,4,5,6
""",
    )

    result = prepare_current_auth_history(input_path, output_dir, run_id="run-1")

    output_path = output_dir / "snapshots" / "current_auth_history_snapshot_real.csv"
    rows = output_path.read_text(encoding="utf-8").splitlines()
    assert result.row_count == 2
    assert rows[0].split(",") == [
        "kpn",
        "vpareadescription",
        "distysegment",
        "P20_PRICE",
        "P50_PRICE",
        "P85_PRICE",
        "n_transactions",
        "quantity_sum",
        "revenue_sum",
        "current_history_run_id",
        "history_snapshot_type",
    ]
    assert "KPN_1,VP_1,SEG_1,8,10,12,2,3.0,34.0,run-1,current_auth_history_real" in rows


def test_prepare_current_auth_history_rejects_missing_keys(tmp_path):
    input_path = tmp_path / "curated_input.csv"
    output_dir = tmp_path / "out"
    write_csv(input_path, "kpn,current_price\nKPN_1,10")

    try:
        prepare_current_auth_history(input_path, output_dir, run_id="run-1")
    except ValueError as exc:
        assert "missing required columns" in str(exc)
    else:
        raise AssertionError("expected ValueError")
