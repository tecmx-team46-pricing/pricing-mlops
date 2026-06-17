import csv

from pricing.scoring import score_recommendations


def test_score_recommendations_writes_versioned_model_output_snapshot(tmp_path):
    feature_table = tmp_path / "feature_table.csv"
    output_path = tmp_path / "snapshots" / "model_output_snapshot.csv"
    feature_table.write_text(
        "\n".join(
            [
                "kpn,vpareadescription,distysegment,P20_PRICE,P50_PRICE,P85_PRICE,revenue_sum",
                "KPN-1,North,Enterprise,8,10,12,100",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = score_recommendations(feature_table, output_path, run_id="score-run")

    assert result.row_count == 1
    assert result.recommendation_source_column == "P50_PRICE"
    with output_path.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["Selected_Optimal_Price"] == "10"
    assert row["scoring_strategy"] == "contract_passthrough_v1"
    assert row["model_output_version"] == "model_output_snapshot_v1"
    assert row["scoring_run_id"] == "score-run"


def test_score_recommendations_rejects_missing_contract_columns(tmp_path):
    feature_table = tmp_path / "feature_table.csv"
    feature_table.write_text("kpn,P50_PRICE\nKPN-1,10\n", encoding="utf-8")

    try:
        score_recommendations(feature_table, tmp_path / "out.csv", run_id="score-run")
    except ValueError as exc:
        assert "missing required columns" in str(exc)
    else:
        raise AssertionError("expected ValueError")
