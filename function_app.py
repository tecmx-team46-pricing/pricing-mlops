from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

ALLOWED_ENVIRONMENTS = {"staging", "validation"}
SAFE_OWNER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
SAFE_BLOB_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./=-]{0,255}$")
REPO_ROOT = Path(__file__).resolve().parent
JOB_FILE = REPO_ROOT / "azureml" / "pricing-mlops-job.yml"


@app.function_name(name="model-flow")
@app.route(route="model-flow", methods=["POST"])
def model_flow(req: func.HttpRequest) -> func.HttpResponse:
    try:
        payload = req.get_json()
    except ValueError:
        payload = {}

    try:
        request = _orchestration_request(payload)
    except ValueError as exc:
        return func.HttpResponse(
            json.dumps({"status": "failed", "error": str(exc)}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        result = submit_azure_ml_job(request)
    except Exception as exc:
        return func.HttpResponse(
            json.dumps({"accepted": False, "error": str(exc)}, sort_keys=True),
            status_code=500,
            mimetype="application/json",
        )

    return func.HttpResponse(
        json.dumps(result, sort_keys=True),
        status_code=202,
        mimetype="application/json",
    )


@app.function_name(name="health")
@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"status": "ok", "role": "azure-ml-orchestrator"}),
        status_code=200,
        mimetype="application/json",
    )


def _orchestration_request(payload: dict[str, object]) -> dict[str, str]:
    request = {
        "subscription_id": _required("AZURE_SUBSCRIPTION_ID", payload),
        "resource_group": _required("AZURE_RESOURCE_GROUP", payload),
        "workspace": _required("AZURE_ML_WORKSPACE", payload),
        "storage_account": _required("AZURE_STORAGE_ACCOUNT", payload),
        "environment": _value("MLOPS_ENVIRONMENT", payload, "staging"),
        "run_owner": _value("MLOPS_RUN_OWNER", payload, "team46"),
        "compute_target": "azure-ml",
        "input_container": _value("MLOPS_CONTAINER_RAW_MASKED", payload, "raw-masked"),
        "input_blob_path": _value("MLOPS_INPUT_BLOB_PATH", payload, "samples/sample_pricing_v1.csv"),
    }
    _validate_request(request)
    request["run_id"] = _value("MLOPS_RUN_ID", payload, _new_run_id())
    request["expected_output_prefix"] = _expected_output_prefix(request)
    return request


def _required(name: str, payload: dict[str, object]) -> str:
    value = _value(name, payload, "")
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _value(name: str, payload: dict[str, object], default: str) -> str:
    value = _payload_value(name, payload) or os.getenv(name) or default
    return str(value)


def _payload_value(env_name: str, payload: dict[str, object]) -> object | None:
    keys = [env_name.lower()]
    if env_name.startswith("MLOPS_"):
        keys.append(env_name.removeprefix("MLOPS_").lower())
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def _validate_request(request: dict[str, str]) -> None:
    if request["environment"] not in ALLOWED_ENVIRONMENTS:
        raise ValueError("environment must be staging or validation")
    if not SAFE_OWNER_RE.fullmatch(request["run_owner"]):
        raise ValueError("run_owner must contain only letters, numbers, underscores, or hyphens")
    input_blob_path = request["input_blob_path"]
    if not input_blob_path or input_blob_path.startswith("/") or ".." in input_blob_path:
        raise ValueError("input_blob_path must be a relative blob path")
    if not SAFE_BLOB_RE.fullmatch(input_blob_path):
        raise ValueError("input_blob_path contains unsupported characters")


def _new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-function")


def _expected_output_prefix(request: dict[str, str]) -> str:
    run_date = request["run_id"][:8]
    return (
        f"environment={request['environment']}/"
        f"compute={request['compute_target']}/"
        f"owner={request['run_owner']}/"
        f"run_date={run_date}/"
        f"run_id={request['run_id']}"
    )


def submit_azure_ml_job(request: dict[str, str]) -> dict[str, str | bool]:
    from azure.ai.ml import MLClient, load_job

    credential = _azure_credential()
    client = MLClient(
        credential,
        request["subscription_id"],
        request["resource_group"],
        request["workspace"],
    )
    job = load_job(source=JOB_FILE)
    for key, value in {
        "storage_account": request["storage_account"],
        "environment": request["environment"],
        "run_owner": request["run_owner"],
        "run_id": request["run_id"],
        "input_blob_path": request["input_blob_path"],
    }.items():
        job.inputs[key]._data = value
    created = client.jobs.create_or_update(job)
    return {
        "accepted": True,
        "azure_ml_job_name": created.name,
        "run_id": request["run_id"],
        "expected_output_prefix": request["expected_output_prefix"],
    }


def _azure_credential():
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

    if os.getenv("MSI_ENDPOINT") or os.getenv("IDENTITY_ENDPOINT"):
        return ManagedIdentityCredential()
    return DefaultAzureCredential()
