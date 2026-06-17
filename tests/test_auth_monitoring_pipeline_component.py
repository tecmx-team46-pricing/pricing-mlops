import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_FILE = ROOT / "azureml" / "pipelines" / "auth_monitoring_pipeline.yml"
RELEASE_MANIFEST = ROOT / "azureml" / "manifests" / "auth-monitoring-release.json"
REGISTER_SCRIPT = ROOT / "scripts" / "register_azureml_components.sh"
REGISTER_ASSETS = ROOT / "scripts" / "azureml" / "register_assets.py"
WORKFLOW_FILE = ROOT / ".github" / "workflows" / "azureml-components.yml"

PIPELINE_VERSION = "0.1.17"
FUNCTIONAL_COMPONENT_VERSION = "0.1.2"
MONITORING_COMPONENT_VERSION = "0.1.3"
FEATURE_ENGINEERING_COMPONENT = "azureml:pricing_mlops_feature_engineering:0.1.0"
PREPARE_CURRENT_HISTORY_COMPONENT = "azureml:pricing_mlops_prepare_current_auth_history:0.1.0"
BUILD_BASELINE_COMPONENT = "azureml:pricing_mlops_build_baseline_snapshot:0.1.0"
PUBLISH_COMPONENT = "azureml:pricing_mlops_publish_outputs:0.1.6"
SIMULATE_COMPONENT = "azureml:pricing_mlops_simulate_operational_handoff:0.1.3"
NOTIFY_COMPONENT = "azureml:pricing_mlops_notify_operational_decision:0.1.0"

EXPECTED_FUNCTIONAL_COMPONENTS = {
    "validate_prepare": ("pricing_mlops_validate_prepare", FUNCTIONAL_COMPONENT_VERSION),
    "build_monitoring_inputs": "pricing_mlops_build_monitoring_inputs",
    "calculate_recommendation_validity": "pricing_mlops_calculate_recommendation_validity",
    "calculate_auth_history_drift": "pricing_mlops_calculate_auth_history_drift",
    "calculate_operational_decision": ("pricing_mlops_calculate_operational_decision", "0.1.6"),
}


def test_auth_monitoring_pipeline_component_composes_registered_components():
    pipeline = yaml.safe_load(PIPELINE_FILE.read_text(encoding="utf-8"))

    assert pipeline["type"] == "pipeline"
    assert pipeline["name"] == "pricing_mlops_auth_monitoring_pipeline"
    assert pipeline["version"] == PIPELINE_VERSION
    assert set(pipeline["jobs"]) == {
        *EXPECTED_FUNCTIONAL_COMPONENTS,
        "feature_engineering",
        "prepare_current_auth_history",
        "simulate_operational_handoff",
        "publish_outputs",
        "notify_operational_decision",
    }
    for job_name, component in EXPECTED_FUNCTIONAL_COMPONENTS.items():
        if isinstance(component, tuple):
            component_name, component_version = component
        else:
            component_name, component_version = component, MONITORING_COMPONENT_VERSION
        job = pipeline["jobs"][job_name]
        assert job["compute"] == "azureml:cpu-cluster"
        assert job["component"] == f"azureml:{component_name}:{component_version}"
        assert job["identity"] == {"type": "managed_identity"}

    feature_engineering_job = pipeline["jobs"]["feature_engineering"]
    assert feature_engineering_job["component"] == FEATURE_ENGINEERING_COMPONENT
    assert feature_engineering_job["identity"] == {"type": "managed_identity"}
    assert (
        feature_engineering_job["inputs"]["previous_step_token"]["path"]
        == "${{parent.jobs.validate_prepare.outputs.flow_token}}"
    )
    assert feature_engineering_job["inputs"]["feature_container"] == "artifacts"
    assert (
        feature_engineering_job["inputs"]["feature_prefix"]
        == "component-state/${{parent.inputs.run_id}}/feature_engineering"
    )

    prepare_current_history_job = pipeline["jobs"]["prepare_current_auth_history"]
    assert prepare_current_history_job["component"] == PREPARE_CURRENT_HISTORY_COMPONENT
    assert prepare_current_history_job["identity"] == {"type": "managed_identity"}
    assert (
        prepare_current_history_job["inputs"]["previous_step_token"]["path"]
        == "${{parent.jobs.feature_engineering.outputs.flow_token}}"
    )
    assert prepare_current_history_job["inputs"]["input_container"] == "artifacts"
    assert prepare_current_history_job["inputs"]["input_blob_path"] == (
        "component-state/${{parent.inputs.run_id}}/feature_engineering/curated/current_auth_features.csv"
    )
    assert (
        pipeline["jobs"]["build_monitoring_inputs"]["inputs"]["previous_step_token"]["path"]
        == "${{parent.jobs.prepare_current_auth_history.outputs.flow_token}}"
    )
    assert pipeline["jobs"]["build_monitoring_inputs"]["inputs"]["current_history_container"] == "artifacts"
    assert pipeline["jobs"]["build_monitoring_inputs"]["inputs"]["current_history_blob_path"] == (
        "component-state/${{parent.inputs.run_id}}/current_auth_history/snapshots/"
        "current_auth_history_snapshot_real.csv"
    )

    simulate_job = pipeline["jobs"]["simulate_operational_handoff"]
    assert simulate_job["component"] == SIMULATE_COMPONENT
    assert simulate_job["identity"] == {"type": "managed_identity"}
    assert (
        simulate_job["inputs"]["previous_step_token"]["path"]
        == "${{parent.jobs.calculate_operational_decision.outputs.flow_token}}"
    )

    publish_job = pipeline["jobs"]["publish_outputs"]
    assert publish_job["component"] == PUBLISH_COMPONENT
    assert publish_job["identity"] == {"type": "managed_identity"}
    assert (
        publish_job["inputs"]["previous_step_token"]["path"]
        == "${{parent.jobs.simulate_operational_handoff.outputs.flow_token}}"
    )
    notify_job = pipeline["jobs"]["notify_operational_decision"]
    assert notify_job["component"] == NOTIFY_COMPONENT
    assert notify_job["identity"] == {"type": "managed_identity"}
    assert (
        notify_job["inputs"]["previous_step_token"]["path"]
        == "${{parent.jobs.publish_outputs.outputs.flow_token}}"
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
    assert manifest["components"]["build_baseline_snapshot"] == BUILD_BASELINE_COMPONENT
    assert manifest["components"]["feature_engineering"] == FEATURE_ENGINEERING_COMPONENT
    assert manifest["components"]["prepare_current_auth_history"] == PREPARE_CURRENT_HISTORY_COMPONENT
    assert manifest["components"]["publish_outputs"] == PUBLISH_COMPONENT
    assert manifest["components"]["simulate_operational_handoff"] == SIMULATE_COMPONENT
    assert manifest["components"]["notify_operational_decision"] == NOTIFY_COMPONENT


def test_register_script_and_workflow_publish_pipeline_component():
    script = REGISTER_SCRIPT.read_text(encoding="utf-8")
    register_python = REGISTER_ASSETS.read_text(encoding="utf-8")
    workflow = yaml.safe_load(WORKFLOW_FILE.read_text(encoding="utf-8"))
    triggers = workflow[True]
    push = triggers["push"]
    steps = workflow["jobs"]["register-components"]["steps"]
    step_text = "\n".join(str(step) for step in steps)

    assert "scripts/azureml/register_assets.py" in script
    assert "AZURE_ML_RELEASE_CONFIG" in script
    assert "config.pipeline.path" in register_python
    assert "ml_client.components.create_or_update" in register_python
    assert "azureml/pipelines/**" in push["paths"]
    assert "azureml/manifests/**" in push["paths"]
    assert "src/pricing/auth_monitoring/**" in push["paths"]
    assert "src/pricing_mlops/monitoring/pipeline/**" in push["paths"]
    assert "python scripts/azureml/deploy_endpoint.py" in step_text
    assert "scripts/invoke_auth_monitoring_batch_endpoint.sh" not in step_text
    assert "actions/upload-artifact@v4" in step_text
    assert "auth-monitoring-release.json" in step_text
