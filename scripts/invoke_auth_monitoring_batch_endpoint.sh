#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-rg-pricing-mlops-main}"
WORKSPACE="${AZURE_ML_WORKSPACE:-mlw-pmlops-06152240}"
ENDPOINT_NAME="${AZURE_ML_BATCH_ENDPOINT:-pricing-auth-monitoring}"
DEPLOYMENT_NAME="${AZURE_ML_BATCH_DEPLOYMENT:-blue}"
STORAGE_ACCOUNT="${AZURE_STORAGE_ACCOUNT:-stpmlops06152240}"
JOB_IDENTITY_CLIENT_ID="${AZURE_ML_JOB_IDENTITY_CLIENT_ID:-2e893571-165f-4930-8d01-c2c0993240b9}"

ENVIRONMENT="${MLOPS_ENVIRONMENT:-staging}"
RUN_OWNER="${MLOPS_RUN_OWNER:-team46}"
RUN_ID="${MLOPS_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-batch-endpoint}"
INPUT_BLOB_PATH="${MLOPS_INPUT_BLOB_PATH:-samples/auth_monitoring_sample.csv}"
BASELINE_SNAPSHOT_CONTAINER="${MLOPS_BASELINE_SNAPSHOT_CONTAINER:-artifacts}"
BASELINE_SNAPSHOT_BLOB_PATH="${MLOPS_BASELINE_SNAPSHOT_BLOB_PATH:-baseline/auth_monitoring_sample_baseline.csv}"
CURRENT_HISTORY_CONTAINER="${MLOPS_CURRENT_HISTORY_CONTAINER:-raw-masked}"
CURRENT_HISTORY_BLOB_PATH="${MLOPS_CURRENT_AUTH_HISTORY_BLOB_PATH:-samples/auth_monitoring_sample.csv}"
MODEL_REPO="${MODEL_REPO_GITHUB:-tecmx-team46-pricing/pricing-mlops}"
MODEL_REF="${MODEL_REPO_REF:-main}"
MODEL_COMMIT_SHA="${MODEL_REPO_COMMIT_SHA:-unknown}"
MONITORING_CONFIG_VERSION="${MLOPS_MONITORING_CONFIG_VERSION:-2026-05-07}"
MONITORING_CONFIG_PATH="${MLOPS_MONITORING_CONFIG_PATH:-configs/drift_thresholds.json}"
WAIT_FOR_COMPLETION="${AZURE_ML_WAIT_FOR_COMPLETION:-false}"
WAIT_TIMEOUT_SECONDS="${AZURE_ML_WAIT_TIMEOUT_SECONDS:-1800}"
WAIT_INTERVAL_SECONDS="${AZURE_ML_WAIT_INTERVAL_SECONDS:-30}"

JOB_NAME="$(
  az ml batch-endpoint invoke \
    --resource-group "${RESOURCE_GROUP}" \
    --workspace-name "${WORKSPACE}" \
    --name "${ENDPOINT_NAME}" \
    --deployment-name "${DEPLOYMENT_NAME}" \
    --experiment-name pricing-mlops-batch-endpoint \
    --set \
      inputs.storage_account="${STORAGE_ACCOUNT}" \
      inputs.environment="${ENVIRONMENT}" \
      inputs.run_owner="${RUN_OWNER}" \
      inputs.run_id="${RUN_ID}" \
      inputs.input_blob_path="${INPUT_BLOB_PATH}" \
      inputs.baseline_snapshot_container="${BASELINE_SNAPSHOT_CONTAINER}" \
      inputs.baseline_snapshot_blob_path="${BASELINE_SNAPSHOT_BLOB_PATH}" \
      inputs.current_history_container="${CURRENT_HISTORY_CONTAINER}" \
      inputs.current_history_blob_path="${CURRENT_HISTORY_BLOB_PATH}" \
      inputs.trigger_type=batch-endpoint \
      inputs.model_repo="${MODEL_REPO}" \
      inputs.model_ref="${MODEL_REF}" \
      inputs.model_commit_sha="${MODEL_COMMIT_SHA}" \
      inputs.monitoring_config_version="${MONITORING_CONFIG_VERSION}" \
      inputs.monitoring_config_path="${MONITORING_CONFIG_PATH}" \
      inputs.job_identity_client_id="${JOB_IDENTITY_CLIENT_ID}" \
    --query name \
    -o tsv
)"

EXPECTED_OUTPUT_PREFIX="environment=${ENVIRONMENT}/compute=azure-ml/trigger=batch-endpoint/owner=${RUN_OWNER}/run_date=${RUN_ID:0:8}/run_id=${RUN_ID}"

cat <<EOF
accepted=true
azure_ml_job_name=${JOB_NAME}
run_id=${RUN_ID}
expected_output_prefix=${EXPECTED_OUTPUT_PREFIX}
EOF

if [[ "${WAIT_FOR_COMPLETION}" == "true" ]]; then
  deadline=$((SECONDS + WAIT_TIMEOUT_SECONDS))
  while true; do
    JOB_STATUS="$(
      az ml job show \
        --resource-group "${RESOURCE_GROUP}" \
        --workspace-name "${WORKSPACE}" \
        --name "${JOB_NAME}" \
        --query status \
        -o tsv
    )"
    echo "azure_ml_job_status=${JOB_STATUS}"
    case "${JOB_STATUS}" in
      Completed)
        exit 0
        ;;
      Failed|Canceled|NotResponding)
        echo "Azure ML job reached terminal failure status: ${JOB_STATUS}" >&2
        exit 1
        ;;
    esac
    if (( SECONDS >= deadline )); then
      echo "Timed out waiting for Azure ML job ${JOB_NAME} after ${WAIT_TIMEOUT_SECONDS}s." >&2
      exit 1
    fi
    sleep "${WAIT_INTERVAL_SECONDS}"
  done
fi
