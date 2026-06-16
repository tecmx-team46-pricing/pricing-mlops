from pricing_mlops.io import materialize_monitoring_outputs


def test_materialize_monitoring_outputs_writes_grouped_artifacts(tmp_path):
    result = materialize_monitoring_outputs(
        output_root=tmp_path,
        snapshots={"baseline.csv": CsvPayload("kpn\nKPN-001\n")},
        logs={"validity.csv": CsvPayload("status\nGreen\n")},
        summaries={"run.csv": CsvPayload("run_readiness_status\nGreen\n")},
        reports={"report.md": "# Report\n"},
    )

    assert (tmp_path / "snapshots" / "baseline.csv").read_text(encoding="utf-8") == "kpn\nKPN-001\n"
    assert (tmp_path / "logs" / "validity.csv").read_text(encoding="utf-8") == "status\nGreen\n"
    assert (tmp_path / "summaries" / "run.csv").read_text(encoding="utf-8") == (
        "run_readiness_status\nGreen\n"
    )
    assert (tmp_path / "reports" / "report.md").read_text(encoding="utf-8") == "# Report\n"
    assert result.output_root == tmp_path
    assert set(result.relative_paths) == {
        "snapshots/baseline.csv",
        "logs/validity.csv",
        "summaries/run.csv",
        "reports/report.md",
    }


def test_materialize_monitoring_outputs_rejects_paths_outside_group(tmp_path):
    try:
        materialize_monitoring_outputs(
            output_root=tmp_path,
            summaries={"../outside.csv": CsvPayload("status\nRed\n")},
        )
    except ValueError as exc:
        assert "../outside.csv" in str(exc)
    else:
        raise AssertionError("Artifact paths must not escape their output group")


class CsvPayload:
    def __init__(self, text):
        self.text = text

    def to_csv(self, path, index=False):
        assert index is False
        path.write_text(self.text, encoding="utf-8")
