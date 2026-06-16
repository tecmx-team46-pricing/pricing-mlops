import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_FILE = ROOT / "azureml" / "pipelines" / "auth_monitoring_pipeline.yml"
RELEASE_MANIFEST = ROOT / "azureml" / "manifests" / "auth-monitoring-release.json"
REGISTER_SCRIPT = ROOT / "scripts" / "register_azureml_components.sh"
WORKFLOW_FILE = ROOT / ".github" / "workflows" / "azureml-components.yml"

PIPELINE_VERSION = "0.1.4"
FUNCTIONAL_COMPONENT_VERSION = "0.1.2"
MONITORING_COMPONENT_VERSION = "0.1.3"
PUBLISH_COMPONENT = "azureml:pricing_mlops_publish_outputs:0.1.2"

EXPECTED_FUNCTIONAL_COMPONENTS = {
    "validate_prepare": ("pricing_mlops_validate_prepare", FUNCTIONAL_COMPONENT_VERSION),
    "build_monitoring_inputs": "pricing_mlops_build_monitoring_inputs",
    "calculate_recommendation_validity": "pricing_mlops_calculate_recommendation_validity",
    "calculate_auth_history_drift": "pricing_mlops_calculate_auth_history_drift",
    "calculate_operational_decision": "pricing_mlops_calculate_operational_decision",
}


def test_auth_monitoring_pipeline_component_composes_registered_components():
    pipeline = yaml.safe_load(PIPELINE_FILE.read_text(encoding="utf-8"))

    assert pipeline["type"] == "pipeline"
    assert pipeline["name"] == "pricing_mlops_auth_monitoring_pipeline"
    assert pipeline["version"] == PIPELINE_VERSION
    assert set(pipeline["jobs"]) == {
        *EXPECTED_FUNCTIONAL_COMPONENTS,
        "publish_outputs",
    }
    for job_name, component in EXPECTED_FUNCTIONAL_COMPONENTS.items():
        if isinstance(component, tuple):
            component_name, component_version = component
        else:
            component_name, component_version = component, MONITORING_COMPONENT_VERSION
        job = pipeline["jobs"][job_name]
        assert job["compute"] == "azureml:serverless"
        assert job["component"] == f"azureml:{component_name}:{component_version}"
        assert job["identity"] == {"type": "user_identity"}

    publish_job = pipeline["jobs"]["publish_outputs"]
    assert publish_job["component"] == PUBLISH_COMPONENT
    assert publish_job["identity"] == {"type": "user_identity"}
    assert (
        publish_job["inputs"]["previous_step_token"]["path"]
        == "${{parent.jobs.calculate_operational_decision.outputs.flow_token}}"
    )


def test_auth_monitoring_release_manifest_matches_pipeline_component():
    pipeline = yaml.safe_load(PIPELINE_FILE.read_text(encoding="utf-8"))
    manifest = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))

    assert manifest["owner_repo"] == "tecmx-team46-pricing/pricing-mlops"
    assert manifest["pipeline_component"] == (
        f"azureml:{pipeline['name']}:{pipeline['version']}"
    )
    for job_name, component in EXPECTED_FUNCTIONAL_COMPONENTS.items():
        if isinstance(component, tuple):
            component_name, component_version = component
        else:
            component_name, component_version = component, MONITORING_COMPONENT_VERSION
        assert manifest["components"][job_name] == (
            f"azureml:{component_name}:{component_version}"
        )
    assert manifest["components"]["publish_outputs"] == PUBLISH_COMPONENT


def test_register_script_and_workflow_publish_pipeline_component():
    script = REGISTER_SCRIPT.read_text(encoding="utf-8")
    workflow = yaml.safe_load(WORKFLOW_FILE.read_text(encoding="utf-8"))
    triggers = workflow[True]
    push = triggers["push"]
    steps = workflow["jobs"]["register-components"]["steps"]
    step_text = "\n".join(str(step) for step in steps)

    assert "azureml/pipelines/auth_monitoring_pipeline.yml" in script
    assert 'register_component_file "${component_file}" "pipeline component"' in script
    assert "azureml/pipelines/**" in push["paths"]
    assert "azureml/manifests/**" in push["paths"]
    assert "src/pricing/auth_monitoring/**" in push["paths"]
    assert "src/pricing_mlops/monitoring/pipeline/**" in push["paths"]
    assert "scripts/deploy_auth_monitoring_batch_endpoint.sh" in step_text
    assert "scripts/invoke_auth_monitoring_batch_endpoint.sh" in step_text
    assert "actions/upload-artifact@v4" in step_text
    assert "auth-monitoring-release.json" in step_text
