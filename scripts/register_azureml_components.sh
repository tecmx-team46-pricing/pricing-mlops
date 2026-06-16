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

component_name_from_file() {
  python - "$1" <<'PY'
import sys
from pathlib import Path

for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    if line.startswith("name:"):
        print(line.split(":", 1)[1].strip())
        break
PY
}

component_version_from_file() {
  python - "$1" <<'PY'
import sys
from pathlib import Path

for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    if line.startswith("version:"):
        print(line.split(":", 1)[1].strip().strip("'\""))
        break
PY
}

register_component_file() {
  local component_file="$1"
  local label="$2"
  local full_path="${REPO_ROOT}/${component_file}"

  if [[ ! -f "${full_path}" ]]; then
    echo "Azure ML ${label} file not found: ${full_path}" >&2
    exit 1
  fi

  local component_name
  local component_version
  component_name="$(component_name_from_file "${full_path}")"
  component_version="$(component_version_from_file "${full_path}")"

  if az ml component show \
    --subscription "${SUBSCRIPTION_ID}" \
    --resource-group "${RESOURCE_GROUP}" \
    --workspace-name "${AZURE_ML_WORKSPACE}" \
    --name "${component_name}" \
    --version "${component_version}" \
    >/dev/null 2>&1; then
    echo "Azure ML ${label} already exists: ${component_name}:${component_version}"
    return
  fi

  echo "Registering Azure ML ${label} from ${component_file}"
  az ml component create \
    --subscription "${SUBSCRIPTION_ID}" \
    --resource-group "${RESOURCE_GROUP}" \
    --workspace-name "${AZURE_ML_WORKSPACE}" \
    --file "${full_path}"
}

component_files=(
  "azureml/components/validate_prepare.yml"
  "azureml/components/build_monitoring_inputs.yml"
  "azureml/components/calculate_recommendation_validity.yml"
  "azureml/components/calculate_auth_history_drift.yml"
  "azureml/components/calculate_operational_decision.yml"
  "azureml/components/publish_outputs.yml"
)

pipeline_component_files=(
  "azureml/pipelines/auth_monitoring_pipeline.yml"
)

az account set --subscription "${SUBSCRIPTION_ID}"

echo "Registering Azure ML environment from azureml/environment.yml"
az ml environment create \
  --subscription "${SUBSCRIPTION_ID}" \
  --resource-group "${RESOURCE_GROUP}" \
  --workspace-name "${AZURE_ML_WORKSPACE}" \
  --file "${REPO_ROOT}/azureml/environment.yml"

for component_file in "${component_files[@]}"; do
  register_component_file "${component_file}" "component"
done

for component_file in "${pipeline_component_files[@]}"; do
  register_component_file "${component_file}" "pipeline component"
done

echo "Azure ML components registered."
