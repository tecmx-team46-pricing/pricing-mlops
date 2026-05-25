from pricing_mlops.artifact_publishing import PublishingConfig


def test_publishing_config_defaults_to_required_azure_blob(monkeypatch):
    monkeypatch.delenv("MLOPS_ARTIFACT_SINKS", raising=False)
    monkeypatch.delenv("MLOPS_OPTIONAL_ARTIFACT_SINKS", raising=False)

    config = PublishingConfig.from_env()

    assert config.enabled_sink_names() == ("azure_blob",)
    assert config.is_required("azure_blob") is True
    assert config.containers["drift_logs"] == "drift-logs"


def test_publishing_config_allows_declarative_optional_sinks(monkeypatch):
    monkeypatch.setenv("MLOPS_ARTIFACT_SINKS", "azure_blob,azure_ml,sql_metadata")
    monkeypatch.setenv("MLOPS_OPTIONAL_ARTIFACT_SINKS", "azure_ml,sql_metadata")
    monkeypatch.setenv("MLOPS_CONTAINER_RUNS", "custom-runs")

    config = PublishingConfig.from_env()

    assert config.enabled_sink_names() == ("azure_blob", "azure_ml", "sql_metadata")
    assert config.is_required("azure_blob") is True
    assert config.is_required("azure_ml") is False
    assert config.is_required("sql_metadata") is False
    assert config.containers["runs"] == "custom-runs"
