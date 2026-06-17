from pathlib import Path

import scripts.components.feature_engineering as component


def test_feature_engineering_component_builds_local_outputs(tmp_path, monkeypatch):
    source = tmp_path / "source.csv"
    output_dir = tmp_path / "outputs"
    source.write_text(
        "\n".join(
            [
                "kpn,vpareadescription,distysegment,current_price,quantity",
                "KPN-1,North,Enterprise,10,2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    def fake_download_blob(storage_account, container, blob_path, destination):
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        Path(destination).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    uploaded = {}

    def fake_upload_tree(storage_account, container, prefix, source_dir):
        uploaded["container"] = container
        uploaded["prefix"] = prefix
        uploaded["source_dir"] = Path(source_dir)

    monkeypatch.setattr(component, "download_blob", fake_download_blob)
    monkeypatch.setattr(component, "upload_tree", fake_upload_tree)
    monkeypatch.setattr(
        "sys.argv",
        [
            "feature_engineering.py",
            "--storage-account",
            "acct",
            "--input-container",
            "raw-masked",
            "--input-blob-path",
            "samples/current.csv",
            "--output-dir",
            str(output_dir),
            "--run-id",
            "run-1",
            "--feature-container",
            "artifacts",
            "--feature-prefix",
            "component-state/run-1/feature_engineering",
        ],
    )

    assert component.main() == 0
    assert (output_dir / "curated" / "current_auth_features.csv").is_file()
    assert (output_dir / "curated" / "feature_table.csv").is_file()
    assert uploaded == {
        "container": "artifacts",
        "prefix": "component-state/run-1/feature_engineering",
        "source_dir": output_dir,
    }
