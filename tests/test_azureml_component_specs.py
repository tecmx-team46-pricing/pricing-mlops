from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
COMPONENT_DIR = ROOT / "azureml" / "components"
REGISTER_SCRIPT = ROOT / "scripts" / "register_azureml_components.sh"
AMLIGNORE = ROOT / ".amlignore"
COMPONENT_VERSION = "0.1.2"
MONITORING_COMPONENT_VERSION = "0.1.3"
RUNTIME_ENVIRONMENT = "azureml:pricing-mlops-runtime:0.1.0"

EXPECTED_COMPONENTS = {
    "validate_prepare": {
        "name": "pricing_mlops_validate_prepare",
        "entrypoint": "scripts/components/validate_prepare.py",
        "inputs": {"storage_account", "input_blob_path", "run_id", "job_identity_client_id"},
    },
    "build_monitoring_inputs": {
        "name": "pricing_mlops_build_monitoring_inputs",
        "step": "build_monitoring_inputs",
        "inputs": {
            "storage_account",
            "run_id",
            "baseline_snapshot_container",
            "baseline_snapshot_blob_path",
            "current_history_container",
            "current_history_blob_path",
            "job_identity_client_id",
            "previous_step_token",
        },
    },
    "calculate_recommendation_validity": {
        "name": "pricing_mlops_calculate_recommendation_validity",
        "step": "calculate_recommendation_validity",
        "inputs": {"storage_account", "run_id", "job_identity_client_id", "previous_step_token"},
    },
    "calculate_auth_history_drift": {
        "name": "pricing_mlops_calculate_auth_history_drift",
        "step": "calculate_auth_history_drift",
        "inputs": {"storage_account", "run_id", "job_identity_client_id", "previous_step_token"},
    },
    "calculate_operational_decision": {
        "name": "pricing_mlops_calculate_operational_decision",
        "step": "calculate_operational_decision",
        "inputs": {"storage_account", "run_id", "job_identity_client_id", "previous_step_token"},
    },
    "publish_outputs": {
        "name": "pricing_mlops_publish_outputs",
        "entrypoint": "scripts/components/publish_outputs.py",
        "inputs": {
            "storage_account",
            "run_id",
            "environment",
            "run_owner",
            "input_blob_path",
            "trigger_type",
            "model_repo",
            "model_ref",
            "model_commit_sha",
            "monitoring_config_version",
            "monitoring_config_path",
            "job_identity_client_id",
            "previous_step_token",
        },
        "outputs": set(),
    },
}


def test_azureml_component_specs_are_registered_units():
    for slug, expected in EXPECTED_COMPONENTS.items():
        component = yaml.safe_load((COMPONENT_DIR / f"{slug}.yml").read_text(encoding="utf-8"))
        expected_version = MONITORING_COMPONENT_VERSION if "step" in expected else COMPONENT_VERSION

        assert component["type"] == "command"
        assert component["name"] == expected["name"]
        assert component["version"] == expected_version
        assert component["code"] == "../.."
        assert component["environment"] == RUNTIME_ENVIRONMENT
        assert set(component["inputs"]) == expected["inputs"]
        if expected.get("outputs", {"flow_token"}):
            assert "flow_token" in component["outputs"]
        else:
            assert "outputs" not in component or component["outputs"] in ({}, None)
        assert "MLOPS_USE_MANAGED_IDENTITY_CREDENTIAL=true" in component["command"]
        assert "AZURE_ML_JOB_IDENTITY_CLIENT_ID=${{inputs.job_identity_client_id}}" in component["command"]
        if "step" in expected:
            assert "python scripts/components/run_monitoring_step.py" in component["command"]
            assert f"--step {expected['step']}" in component["command"]
        else:
            assert expected["entrypoint"] in component["command"]
        assert "pip install" not in component["command"]


def test_register_components_script_publishes_every_component():
    script = REGISTER_SCRIPT.read_text(encoding="utf-8")

    assert "AZURE_SUBSCRIPTION_ID" in script
    assert "AZURE_RESOURCE_GROUP" in script
    assert "AZURE_ML_WORKSPACE" in script
    assert "az ml environment create" in script
    assert "azureml/environment.yml" in script
    assert "az ml component show" in script
    assert "az ml component create" in script
    assert "already exists" in script
    for slug in EXPECTED_COMPONENTS:
        assert f"azureml/components/{slug}.yml" in script


def test_runtime_environment_spec_is_versioned_in_model_repo():
    environment = yaml.safe_load((ROOT / "azureml" / "environment.yml").read_text(encoding="utf-8"))
    conda = yaml.safe_load((ROOT / "azureml" / "conda.yml").read_text(encoding="utf-8"))
    pip_dependencies = next(
        item["pip"] for item in conda["dependencies"] if isinstance(item, dict) and "pip" in item
    )

    assert environment["name"] == "pricing-mlops-runtime"
    assert str(environment["version"]) == "0.1.0"
    assert environment["conda_file"] == "conda.yml"
    assert "openmpi4.1.0-ubuntu22.04" in environment["image"]
    assert conda["name"] == "pricing-mlops-runtime"
    assert "python=3.11" in conda["dependencies"]
    assert "azure-ai-ml>=1.32.0" in pip_dependencies
    assert "azure-identity>=1.17.0" in pip_dependencies
    assert "azure-storage-blob>=12.20.0" in pip_dependencies


def test_amlignore_keeps_component_snapshots_small_and_masked():
    ignored = AMLIGNORE.read_text(encoding="utf-8")

    for pattern in ("notebooks/", "tests/", "docs/", "data/samples/unmasked/", ".github/"):
        assert pattern in ignored


def test_model_repo_registers_components_from_github_actions():
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "azureml-components.yml").read_text(encoding="utf-8")
    )
    triggers = workflow[True]
    push = triggers["push"]
    steps = workflow["jobs"]["register-components"]["steps"]
    step_text = "\n".join(str(step) for step in steps)

    assert push["branches"] == ["main"]
    assert "azureml/components/**" in push["paths"]
    assert "azureml/endpoints/**" in push["paths"]
    assert "scripts/register_azureml_components.sh" in push["paths"]
    assert "scripts/deploy_auth_monitoring_batch_endpoint.sh" in push["paths"]
    assert "scripts/invoke_auth_monitoring_batch_endpoint.sh" not in push["paths"]
    assert workflow["permissions"] == {"contents": "read", "id-token": "write"}
    assert workflow["jobs"]["register-components"]["environment"] == "staging"
    assert "azure/login@v2" in step_text
    assert "scripts/register_azureml_components.sh" in step_text
    assert "scripts/invoke_auth_monitoring_batch_endpoint.sh" not in step_text
