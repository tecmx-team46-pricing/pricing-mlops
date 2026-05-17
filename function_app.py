from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from uuid import uuid4

import azure.functions as func

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scripts.run_azure_storage_flow import AzureStorageFlowRequest, run_azure_storage_flow


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(
            {
                "status": "ok",
                "message": os.getenv("PRICING_MLOPS_HELLO_MESSAGE", "hello world"),
                "workload": "pricing-mlops",
                "environment": os.getenv("PRICING_MLOPS_ENVIRONMENT", "unknown"),
            }
        ),
        mimetype="application/json",
    )


@app.route(route="model-flow", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def model_flow(req: func.HttpRequest) -> func.HttpResponse:
    body = _json_body(req)
    environment = _value(body, "environment", os.getenv("MLOPS_ENVIRONMENT", "staging"))
    run_owner = _value(body, "run_owner", os.getenv("MLOPS_RUN_OWNER", "team46"))
    input_blob_path = _value(
        body,
        "input_blob_path",
        os.getenv("MLOPS_INPUT_BLOB_PATH", "samples/sample_pricing_v1.csv"),
    )
    run_id = _value(body, "run_id", None) or f"azfunc-{uuid4().hex[:12]}"

    request = AzureStorageFlowRequest(
        storage_account=_required_env("AZURE_STORAGE_ACCOUNT"),
        environment=environment,
        run_owner=run_owner,
        run_id=run_id,
        input_container=os.getenv("MLOPS_CONTAINER_RAW_MASKED", "raw-masked"),
        input_blob_path=input_blob_path,
        containers={
            "curated": os.getenv("MLOPS_CONTAINER_CURATED", "curated"),
            "runs": os.getenv("MLOPS_CONTAINER_RUNS", "runs"),
            "snapshots": os.getenv("MLOPS_CONTAINER_SNAPSHOTS", "snapshots"),
            "drift_logs": os.getenv("MLOPS_CONTAINER_DRIFT_LOGS", "drift-logs"),
            "reports": os.getenv("MLOPS_CONTAINER_REPORTS", "reports"),
            "artifacts": os.getenv("MLOPS_CONTAINER_ARTIFACTS", "artifacts"),
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
        mimetype="application/json",
    )


def _json_body(req: func.HttpRequest) -> dict[str, object]:
    try:
        body = req.get_json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def _value(body: dict[str, object], key: str, default: str | None) -> str | None:
    value = body.get(key)
    if value is None or value == "":
        return default
    return str(value)


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required app setting: {name}")
    return value
