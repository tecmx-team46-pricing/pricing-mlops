#!/usr/bin/env bash
set -euo pipefail

STORAGE_ACCOUNT="${AZURE_STORAGE_ACCOUNT:-stpmlops06152240}"
RUN_ID="20260621T025500Z-new-auth-inputs"
PREFIX="environment=staging/compute=azure-ml/trigger=batch-endpoint/owner=team46/run_date=20260621/run_id=${RUN_ID}"
OUT_DIR="${1:-/tmp/auth-monitoring-20260621-new-auth-inputs}"

mkdir -p "${OUT_DIR}/inputs"

az storage blob download \
  --account-name "${STORAGE_ACCOUNT}" \
  --auth-mode login \
  --container-name baseline \
  --name auth-monitoring/input6mothback/masked_output_recommendations_2.csv \
  --file "${OUT_DIR}/inputs/masked_output_recommendations_2.csv" \
  --overwrite true

az storage blob download \
  --account-name "${STORAGE_ACCOUNT}" \
  --auth-mode login \
  --container-name raw-masked \
  --name auth-monitoring/input-avance4-current/masked_current_auth_dataset.csv \
  --file "${OUT_DIR}/inputs/masked_current_auth_dataset.csv" \
  --overwrite true

for container in runs snapshots drift-logs reports artifacts; do
  az storage blob download-batch \
    --account-name "${STORAGE_ACCOUNT}" \
    --auth-mode login \
    --source "${container}" \
    --destination "${OUT_DIR}/${container}" \
    --pattern "${PREFIX}/*" \
    --overwrite true
done

cat <<EOF
downloaded=true
run_id=${RUN_ID}
output_dir=${OUT_DIR}
EOF
