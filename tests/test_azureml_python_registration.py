from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / "configs" / "azureml_auth_monitoring.yml"
MANIFEST_FILE = ROOT / "azureml" / "manifests" / "auth-monitoring-release.json"
WORKFLOW_FILE = ROOT / ".github" / "workflows" / "azureml-components.yml"


def test_azureml_release_config_lists_existing_assets():
    config = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))

    asset_paths = [
        config["environment"],
        *config["components"],
        config["pipeline"],
        config["endpoint"]["endpoint_file"],
        config["endpoint"]["deployment_file"],
        config["manifest"],
    ]

    for relative_path in asset_paths:
        assert (ROOT / relative_path).is_file(), relative_path


def test_azureml_release_config_matches_auth_monitoring_contract():
    config = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))

    assert config["subscription_name"] == "Tecmx"
    assert config["resource_group"] == "rg-pricing-mlops-main"
    assert config["workspace"] == "mlw-pmlops-06152240"
    assert config["endpoint"]["name"] == "pricing-auth-monitoring"
    assert config["endpoint"]["deployment"] == "blue"
    assert config["pipeline"] == "azureml/pipelines/auth_monitoring_pipeline.yml"
    assert config["manifest"] == "azureml/manifests/auth-monitoring-release.json"
    assert "azureml/components/validate_prepare.yml" in config["components"]
    assert "azureml/components/publish_outputs.yml" in config["components"]
