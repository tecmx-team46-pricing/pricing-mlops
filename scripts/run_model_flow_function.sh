#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"
PLATFORM_SCRIPT="${PRICING_MLOPS_PLATFORM_REPO:-${WORKSPACE_ROOT}/pricing-mlops-platform}/mlops/scripts/run_model_flow_function.sh"

if [[ ! -x "${PLATFORM_SCRIPT}" ]]; then
  echo "Azure Function operation moved to pricing-mlops-platform." >&2
  echo "Set PRICING_MLOPS_PLATFORM_REPO or run:" >&2
  echo "  ../pricing-mlops-platform/mlops/scripts/run_model_flow_function.sh ${*}" >&2
  exit 1
fi

exec "${PLATFORM_SCRIPT}" "$@"
