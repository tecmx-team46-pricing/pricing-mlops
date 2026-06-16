from pathlib import Path

import yaml

from scripts.azureml.client import AzureMlSettings
from scripts.azureml.config import load_release_config


ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / "configs" / "azureml_auth_monitoring.yml"
MANIFEST_FILE = ROOT / "azureml" / "manifests" / "auth-monitoring-release.json"
WORKFLOW_FILE = ROOT / ".github" / "workflows" / "azureml-components.yml"
REGISTER_ASSETS = ROOT / "scripts" / "azureml" / "register_assets.py"
REGISTER_WRAPPER = ROOT / "scripts" / "register_azureml_components.sh"
DEPLOY_ENDPOINT = ROOT / "scripts" / "azureml" / "deploy_endpoint.py"
DEPLOY_WRAPPER = ROOT / "scripts" / "deploy_auth_monitoring_batch_endpoint.sh"


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


def test_load_release_config_resolves_paths():
    config = load_release_config(CONFIG_FILE, repo_root=ROOT)

    assert config.subscription_name == "Tecmx"
    assert config.resource_group == "rg-pricing-mlops-main"
    assert config.workspace == "mlw-pmlops-06152240"
    assert config.environment.path == ROOT / "azureml/environment.yml"
    assert len(config.components) == 6
    assert config.pipeline.path == ROOT / "azureml/pipelines/auth_monitoring_pipeline.yml"
    assert config.endpoint.name == "pricing-auth-monitoring"
    assert config.endpoint.deployment == "blue"
    assert config.manifest.path == ROOT / "azureml/manifests/auth-monitoring-release.json"


def test_azureml_settings_uses_env_overrides(monkeypatch):
    config = load_release_config(CONFIG_FILE, repo_root=ROOT)
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "sub-from-env")
    monkeypatch.setenv("AZURE_RESOURCE_GROUP", "rg-from-env")
    monkeypatch.setenv("AZURE_ML_WORKSPACE", "workspace-from-env")

    settings = AzureMlSettings.from_config(config)

    assert settings.subscription_id == "sub-from-env"
    assert settings.resource_group == "rg-from-env"
    assert settings.workspace == "workspace-from-env"


def test_register_assets_uses_python_sdk_loaders():
    source = REGISTER_ASSETS.read_text(encoding="utf-8")

    assert "load_component" in source
    assert "load_environment" in source
    assert "ml_client.components.create_or_update" in source
    assert "ml_client.environments.create_or_update" in source
    assert "az ml component create" not in source


def test_register_shell_wrapper_delegates_to_python():
    source = REGISTER_WRAPPER.read_text(encoding="utf-8")

    assert "python" in source
    assert "scripts/azureml/register_assets.py" in source
    assert "az ml component create" not in source


def test_deploy_endpoint_uses_python_sdk_batch_clients():
    source = DEPLOY_ENDPOINT.read_text(encoding="utf-8")

    assert "load_batch_endpoint" in source
    assert "load_batch_deployment" in source
    assert "ml_client.batch_endpoints.begin_create_or_update" in source
    assert "ml_client.batch_deployments.begin_create_or_update" in source
    assert "az ml batch-deployment create" not in source


def test_deploy_shell_wrapper_delegates_to_python():
    source = DEPLOY_WRAPPER.read_text(encoding="utf-8")

    assert "python" in source
    assert "scripts/azureml/deploy_endpoint.py" in source
    assert "az ml batch-deployment create" not in source
