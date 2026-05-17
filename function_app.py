from __future__ import annotations

import json
import os

import azure.functions as func

from scripts.run_azure_storage_flow import AzureStorageFlowRequest, run_azure_storage_flow

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="model-flow", methods=["POST"])
def model_flow(req: func.HttpRequest) -> func.HttpResponse:
    try:
        payload = req.get_json()
    except ValueError:
        payload = {}

    request = AzureStorageFlowRequest(
        storage_account=_required("AZURE_STORAGE_ACCOUNT", payload),
        environment=payload.get("environment") or os.getenv("MLOPS_ENVIRONMENT", "staging"),
        run_owner=payload.get("run_owner") or os.getenv("MLOPS_RUN_OWNER", "team46"),
        compute_target=payload.get("compute_target") or os.getenv("MLOPS_COMPUTE_TARGET", "functions"),
        run_id=payload.get("run_id") or os.getenv("MLOPS_RUN_ID"),
        input_container=payload.get("input_container")
        or os.getenv("MLOPS_CONTAINER_RAW_MASKED", "raw-masked"),
        input_blob_path=payload.get("input_blob_path")
        or os.getenv("MLOPS_INPUT_BLOB_PATH", "samples/sample_pricing_v1.csv"),
        containers={
            "curated": payload.get("curated_container")
            or os.getenv("MLOPS_CONTAINER_CURATED", "curated"),
            "runs": payload.get("runs_container") or os.getenv("MLOPS_CONTAINER_RUNS", "runs"),
            "snapshots": payload.get("snapshots_container")
            or os.getenv("MLOPS_CONTAINER_SNAPSHOTS", "snapshots"),
            "drift_logs": payload.get("drift_logs_container")
            or os.getenv("MLOPS_CONTAINER_DRIFT_LOGS", "drift-logs"),
            "reports": payload.get("reports_container") or os.getenv("MLOPS_CONTAINER_REPORTS", "reports"),
            "artifacts": payload.get("artifacts_container")
            or os.getenv("MLOPS_CONTAINER_ARTIFACTS", "artifacts"),
        },
    )

    try:
        result = run_azure_storage_flow(request)
    except Exception as exc:
        return func.HttpResponse(
            json.dumps({"status": "failed", "error": str(exc)}),
            status_code=500,
            mimetype="application/json",
        )

    return func.HttpResponse(
        json.dumps(
            {
                "status": "succeeded",
                "run_id": result.run_id,
                "row_count": result.row_count,
                "uploaded_blobs": result.uploaded_blobs,
            },
            sort_keys=True,
        ),
        status_code=200,
        mimetype="application/json",
    )


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"status": "ok", "compute_target": "functions"}),
        status_code=200,
        mimetype="application/json",
    )


def _required(name: str, payload: dict[str, object]) -> str:
    value = payload.get(_payload_key(name)) or os.getenv(name)
    if not value:
        raise ValueError(f"{name} is required")
    return str(value)


def _payload_key(env_name: str) -> str:
    return env_name.lower()
