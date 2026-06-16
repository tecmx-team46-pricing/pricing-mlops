#!/usr/bin/env bash
set -euo pipefail

SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID:-}"
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-}"
AZURE_ML_WORKSPACE="${AZURE_ML_WORKSPACE:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

require_value() {
  local name="$1"
  local value="$2"
  if [[ -z "${value}" ]]; then
    echo "${name} is required." >&2
    exit 1
  fi
}

require_value AZURE_SUBSCRIPTION_ID "${SUBSCRIPTION_ID}"
require_value AZURE_RESOURCE_GROUP "${RESOURCE_GROUP}"
require_value AZURE_ML_WORKSPACE "${AZURE_ML_WORKSPACE}"

component_files=(
  "azureml/components/validate_prepare.yml"
  "azureml/components/build_monitoring_inputs.yml"
  "azureml/components/calculate_recommendation_validity.yml"
  "azureml/components/calculate_auth_history_drift.yml"
  "azureml/components/calculate_operational_decision.yml"
)

az account set --subscription "${SUBSCRIPTION_ID}"

echo "Registering Azure ML environment from azureml/environment.yml"
az ml environment create \
  --subscription "${SUBSCRIPTION_ID}" \
  --resource-group "${RESOURCE_GROUP}" \
  --workspace-name "${AZURE_ML_WORKSPACE}" \
  --file "${REPO_ROOT}/azureml/environment.yml"

for component_file in "${component_files[@]}"; do
  if [[ ! -f "${REPO_ROOT}/${component_file}" ]]; then
    echo "Azure ML component file not found: ${REPO_ROOT}/${component_file}" >&2
    exit 1
  fi
  echo "Registering Azure ML component from ${component_file}"
  az ml component create \
    --subscription "${SUBSCRIPTION_ID}" \
    --resource-group "${RESOURCE_GROUP}" \
    --workspace-name "${AZURE_ML_WORKSPACE}" \
    --file "${REPO_ROOT}/${component_file}"
done

echo "Azure ML components registered."
