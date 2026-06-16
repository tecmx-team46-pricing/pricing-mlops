#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

python "${REPO_ROOT}/scripts/azureml/register_assets.py" \
  --config "${AZURE_ML_RELEASE_CONFIG:-configs/azureml_auth_monitoring.yml}"
