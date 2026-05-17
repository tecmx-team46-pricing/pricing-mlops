#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-staging}"
EXPECTED_SUBSCRIPTION_NAME="${AZURE_SUBSCRIPTION_NAME:-<azure-subscription-name>}"
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-rg-pricing-mlops-${ENVIRONMENT}}"
FUNCTION_APP="${AZURE_FUNCTION_APP:-}"

if [[ "${ENVIRONMENT}" != "staging" && "${ENVIRONMENT}" != "validation" ]]; then
  echo "Unsupported environment for Function publish: ${ENVIRONMENT}" >&2
  echo "Allowed environments: staging, validation" >&2
  exit 1
fi

if [[ -z "${FUNCTION_APP}" ]]; then
  FUNCTION_APP="$(az functionapp list \
    --resource-group "${RESOURCE_GROUP}" \
    --query "[?contains(name, 'func-pricing-mlops')].name | [0]" -o tsv)"
fi

if [[ -z "${FUNCTION_APP}" ]]; then
  echo "Function App not found. Set AZURE_FUNCTION_APP or deploy platform first." >&2
  exit 1
fi

ACTIVE_SUBSCRIPTION_NAME="$(az account show --query name -o tsv 2>/dev/null || true)"

if [[ -z "${ACTIVE_SUBSCRIPTION_NAME}" ]]; then
  echo "Run az login and select the subscription first." >&2
  exit 1
fi

if [[ "${ACTIVE_SUBSCRIPTION_NAME}" != "${EXPECTED_SUBSCRIPTION_NAME}" ]]; then
  echo "Active subscription is '${ACTIVE_SUBSCRIPTION_NAME}', expected '${EXPECTED_SUBSCRIPTION_NAME}'." >&2
  echo "Run: az account set --subscription \"${EXPECTED_SUBSCRIPTION_NAME}\"" >&2
  exit 1
fi

PACKAGE_DIR="$(mktemp -d)"
PACKAGE_PATH="${PACKAGE_DIR}/pricing-mlops-function.zip"
trap 'rm -rf "${PACKAGE_DIR}"' EXIT

zip -qr "${PACKAGE_PATH}" \
  function_app.py \
  host.json \
  requirements.txt \
  pyproject.toml \
  azureml \
  scripts \
  src \
  -x '*/__pycache__/*' '*.pyc' '.pytest_cache/*' 'runs/*' '.venv/*'

az functionapp deployment source config-zip \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${FUNCTION_APP}" \
  --src "${PACKAGE_PATH}" \
  --build-remote true

echo "Published Function App: ${FUNCTION_APP}"
