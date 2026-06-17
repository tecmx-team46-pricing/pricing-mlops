import csv

from pricing.features import build_current_auth_features


def test_build_current_auth_features_aggregates_masked_pricing_rows(tmp_path):
    input_path = tmp_path / "masked_current.csv"
    output_dir = tmp_path / "features"
    input_path.write_text(
        "\n".join(
            [
                "kpn,vpareadescription,distysegment,current_price,quantity",
                "KPN-1,North,Enterprise,10,2",
                "KPN-1,North,Enterprise,20,3",
                "KPN-2,South,SMB,5,4",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = build_current_auth_features(input_path, output_dir, run_id="run-1")

    assert result.row_count == 2
    assert result.current_auth_features_path == output_dir / "curated" / "current_auth_features.csv"
    assert result.feature_table_path == output_dir / "curated" / "feature_table.csv"
    with result.current_auth_features_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    first = rows[0]
    assert first["kpn"] == "KPN-1"
    assert first["n_transactions"] == "2"
    assert float(first["quantity_sum"]) == 5.0
    assert float(first["revenue_sum"]) == 80.0
    assert float(first["P50_PRICE"]) == 15.0
    assert first["feature_engineering_run_id"] == "run-1"


def test_build_current_auth_features_preserves_existing_auth_percentiles(tmp_path):
    input_path = tmp_path / "masked_current.csv"
    output_dir = tmp_path / "features"
    input_path.write_text(
        "\n".join(
            [
                "kpn,vpareadescription,distysegment,current_price,quantity,P20_PRICE,P50_PRICE,P85_PRICE",
                "KPN-1,North,Enterprise,10,2,8,11,14",
                "KPN-1,North,Enterprise,20,3,8,11,14",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    build_current_auth_features(input_path, output_dir, run_id="run-1")

    with (output_dir / "curated" / "current_auth_features.csv").open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["P20_PRICE"] == "8.0"
    assert row["P50_PRICE"] == "11.0"
    assert row["P85_PRICE"] == "14.0"


def test_build_current_auth_features_requires_operational_keys(tmp_path):
    input_path = tmp_path / "bad.csv"
    input_path.write_text("kpn,current_price\nKPN-1,10\n", encoding="utf-8")

    try:
        build_current_auth_features(input_path, tmp_path / "features", run_id="run-1")
    except ValueError as exc:
        assert "missing required columns" in str(exc)
    else:
        raise AssertionError("expected ValueError")
