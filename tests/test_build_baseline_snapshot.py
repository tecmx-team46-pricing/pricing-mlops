from pathlib import Path

from pricing.baseline import build_baseline_snapshot


def test_build_baseline_snapshot_selects_contract_columns(tmp_path):
    feature_table = tmp_path / "feature_table.csv"
    output_path = tmp_path / "model_output_snapshot.csv"
    feature_table.write_text(
        "kpn,vpareadescription,distysegment,Balanced,P20_PRICE,P50_PRICE,P85_PRICE,revenue_sum\n"
        "KPN_1,VP_1,SEG_1,10,8,10,12,100\n",
        encoding="utf-8",
    )

    result = build_baseline_snapshot(feature_table, output_path, run_id="baseline-run")

    text = output_path.read_text(encoding="utf-8")
    assert result.row_count == 1
    assert result.recommendation_column == "Balanced"
    assert "baseline-run" in text
    assert "baseline_mlops_pricing_v1" in text
    assert "model_output_snapshot_v1" in text


def test_build_baseline_snapshot_rejects_missing_recommendation_column(tmp_path):
    feature_table = tmp_path / "feature_table.csv"
    output_path = tmp_path / "model_output_snapshot.csv"
    feature_table.write_text(
        "kpn,vpareadescription,distysegment,P20_PRICE,P50_PRICE,P85_PRICE\n"
        "KPN_1,VP_1,SEG_1,8,10,12\n",
        encoding="utf-8",
    )

    try:
        build_baseline_snapshot(feature_table, output_path, run_id="baseline-run")
    except ValueError as exc:
        assert "missing recommendation column" in str(exc)
    else:
        raise AssertionError("expected ValueError")
