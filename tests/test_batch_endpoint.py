import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT_DIR = ROOT / "azureml" / "endpoints"
MANIFEST_FILE = ROOT / "azureml" / "manifests" / "auth-monitoring-release.json"
SCRIPTS_DIR = ROOT / "scripts"


def test_auth_monitoring_batch_endpoint_targets_repo_owned_pipeline_component():
    endpoint = yaml.safe_load((ENDPOINT_DIR / "auth-monitoring-batch-endpoint.yml").read_text())
    deployment = yaml.safe_load((ENDPOINT_DIR / "auth-monitoring-batch-deployment.yml").read_text())
    manifest = json.loads(MANIFEST_FILE.read_text())

    assert endpoint["name"] == "pricing-auth-monitoring"
    assert endpoint["auth_mode"] == "aad_token"
    assert deployment["endpoint_name"] == endpoint["name"]
    assert deployment["name"] == "blue"
    assert deployment["type"] == "pipeline"
    assert deployment["component"] == manifest["pipeline_component"]
    assert deployment["component"] == "azureml:pricing_mlops_auth_monitoring_pipeline:0.1.7"
    assert deployment["settings"]["default_compute"] == "cpu-cluster"
    assert deployment["settings"]["continue_on_step_failure"] is False


def test_deploy_script_promotes_manifest_pipeline_component():
    deploy_script = (SCRIPTS_DIR / "deploy_auth_monitoring_batch_endpoint.sh").read_text()
    invoke_script = (SCRIPTS_DIR / "invoke_auth_monitoring_batch_endpoint.sh").read_text()

    assert "azureml/endpoints/auth-monitoring-batch-endpoint.yml" in deploy_script
    assert "azureml/endpoints/auth-monitoring-batch-deployment.yml" in deploy_script
    assert "azureml/manifests/auth-monitoring-release.json" in deploy_script
    assert "az ml component show" in deploy_script
    assert "az ml component create" not in deploy_script
    assert "az ml batch-endpoint create" in deploy_script
    assert "az ml batch-deployment create" in deploy_script
    assert "AZURE_ML_PIPELINE_COMPONENT" in deploy_script

    assert "az ml batch-endpoint invoke" in invoke_script
    assert "AZURE_ML_WAIT_FOR_COMPLETION" in invoke_script
    assert "az ml job show" in invoke_script
    assert "--deployment-name" in invoke_script
    assert "--experiment-name pricing-mlops-batch-endpoint" in invoke_script
    assert "--set" in invoke_script
    assert "functionapp" not in invoke_script
