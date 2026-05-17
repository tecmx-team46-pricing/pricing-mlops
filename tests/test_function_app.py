import json

import azure.functions as func

import function_app


def test_orchestration_request_rejects_sandbox(monkeypatch):
    _set_required_env(monkeypatch)

    try:
        function_app._orchestration_request(
            {
                "environment": "sandbox-local",
                "run_owner": "team46",
                "input_blob_path": "samples/sample_pricing_v1.csv",
            }
        )
    except ValueError as exc:
        assert "environment" in str(exc)
    else:
        raise AssertionError("sandbox environment should be rejected")


def test_orchestration_request_builds_expected_prefix(monkeypatch):
    _set_required_env(monkeypatch)

    request = function_app._orchestration_request(
        {
            "environment": "staging",
            "run_owner": "team46",
            "input_blob_path": "samples/sample_pricing_v1.csv",
            "mlops_run_id": "20260517T000000Z-function",
        }
    )

    assert request["compute_target"] == "azure-ml"
    assert request["run_id"] == "20260517T000000Z-function"
    assert request["expected_output_prefix"] == (
        "environment=staging/compute=azure-ml/owner=team46/"
        "run_date=20260517/run_id=20260517T000000Z-function"
    )


def test_model_flow_submits_aml_job(monkeypatch):
    _set_required_env(monkeypatch)
    submitted = {}

    def fake_submit(request):
        submitted.update(request)
        return {
            "accepted": True,
            "azure_ml_job_name": "test_job",
            "run_id": request["run_id"],
            "expected_output_prefix": request["expected_output_prefix"],
        }

    monkeypatch.setattr(function_app, "submit_azure_ml_job", fake_submit)
    request = func.HttpRequest(
        method="POST",
        url="/api/model-flow",
        body=json.dumps(
            {
                "environment": "staging",
                "run_owner": "team46",
                "input_blob_path": "samples/sample_pricing_v1.csv",
                "mlops_run_id": "20260517T000000Z-function",
            }
        ).encode(),
        headers={"content-type": "application/json"},
    )

    response = function_app.model_flow(request)
    body = json.loads(response.get_body())

    assert response.status_code == 202
    assert body["accepted"] is True
    assert body["azure_ml_job_name"] == "test_job"
    assert submitted["run_id"] == "20260517T000000Z-function"


def test_apply_job_inputs_updates_loaded_azure_ml_defaults():
    from azure.ai.ml import load_job

    job = load_job(source="azureml/pricing-mlops-job.yml")
    function_app._apply_job_inputs(job, {"run_id": "run-from-function"})

    assert job._to_dict()["inputs"]["run_id"] == "run-from-function"
    assert job.component.inputs["run_id"]["default"] == "run-from-function"


def test_model_flow_rejects_unsafe_owner(monkeypatch):
    _set_required_env(monkeypatch)
    request = func.HttpRequest(
        method="POST",
        url="/api/model-flow",
        body=json.dumps(
            {
                "environment": "staging",
                "run_owner": "../team46",
                "input_blob_path": "samples/sample_pricing_v1.csv",
            }
        ).encode(),
        headers={"content-type": "application/json"},
    )

    response = function_app.model_flow(request)

    assert response.status_code == 400
    assert b"run_owner" in response.get_body()


def _set_required_env(monkeypatch):
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "<test-subscription-id>")
    monkeypatch.setenv("AZURE_RESOURCE_GROUP", "rg-pricing-mlops-staging")
    monkeypatch.setenv("AZURE_ML_WORKSPACE", "mlw-pricing-mlops-staging-<suffix>")
    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT", "<mlops-storage-account>")
