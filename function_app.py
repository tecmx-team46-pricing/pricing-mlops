from __future__ import annotations

import json
import os

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


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

    return func.HttpResponse(
        json.dumps(
            {
                "status": "prepared",
                "message": "Azure Functions is the orchestrator. It must submit an Azure ML job; it does not run scoring locally.",
                "request": request,
            },
            sort_keys=True,
        ),
        status_code=202,
        mimetype="application/json",
    )


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"status": "ok", "role": "azure-ml-orchestrator"}),
        status_code=200,
        mimetype="application/json",
    )


def _orchestration_request(payload: dict[str, object]) -> dict[str, str]:
    return {
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


def _required(name: str, payload: dict[str, object]) -> str:
    value = _value(name, payload, "")
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _value(name: str, payload: dict[str, object], default: str) -> str:
    value = payload.get(_payload_key(name)) or os.getenv(name) or default
    return str(value)


def _payload_key(env_name: str) -> str:
    return env_name.lower()
