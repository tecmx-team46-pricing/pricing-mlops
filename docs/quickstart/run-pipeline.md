# Quick Start: Correr Pipeline

Esta guia corre el batch endpoint AUTH monitoring con datos masked ya cargados en Storage.

## Variables Requeridas

```bash
export AZURE_RESOURCE_GROUP=<resource-group>
export AZURE_ML_WORKSPACE=<workspace>
export AZURE_STORAGE_ACCOUNT=<storage-account>
export AZURE_ML_JOB_IDENTITY_CLIENT_ID=<managed-identity-client-id>
```

Opcionalmente, si el endpoint tiene un nombre distinto al default:

```bash
export AZURE_ML_BATCH_ENDPOINT=pricing-auth-monitoring
export AZURE_ML_BATCH_DEPLOYMENT=blue
```

## Subir Inputs Masked

No subir datos reales a git. Los inputs van directo a Storage.

```bash
az storage blob upload \
  --account-name "$AZURE_STORAGE_ACCOUNT" \
  --auth-mode login \
  --container-name baseline \
  --name auth-monitoring/input6mothback/masked_output_recommendations_2.csv \
  --file "data/inbox/input6mothback/masked_output_recommendations (2).csv" \
  --overwrite true

az storage blob upload \
  --account-name "$AZURE_STORAGE_ACCOUNT" \
  --auth-mode login \
  --container-name raw-masked \
  --name auth-monitoring/input-avance4-current/masked_current_auth_dataset.csv \
  --file data/inbox/input_avance4_current/masked_current_auth_dataset.csv \
  --overwrite true
```

## Invocar Endpoint

```bash
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-auth-monitoring"

AZURE_ML_WAIT_FOR_COMPLETION=true \
AZURE_ML_WAIT_TIMEOUT_SECONDS=7200 \
AZURE_ML_WAIT_INTERVAL_SECONDS=30 \
MLOPS_ENVIRONMENT=staging \
MLOPS_RUN_OWNER=team46 \
MLOPS_RUN_ID="$RUN_ID" \
MLOPS_BASELINE_SNAPSHOT_CONTAINER=baseline \
MLOPS_BASELINE_SNAPSHOT_BLOB_PATH=auth-monitoring/input6mothback/masked_output_recommendations_2.csv \
MLOPS_INPUT_BLOB_PATH=auth-monitoring/input-avance4-current/masked_current_auth_dataset.csv \
MLOPS_CURRENT_HISTORY_CONTAINER=raw-masked \
MLOPS_CURRENT_AUTH_HISTORY_BLOB_PATH=auth-monitoring/input-avance4-current/masked_current_auth_dataset.csv \
MODEL_REPO_REF="$(git branch --show-current)" \
MODEL_REPO_COMMIT_SHA="$(git rev-parse --short HEAD)" \
scripts/invoke_auth_monitoring_batch_endpoint.sh
```

El script imprime:

```text
accepted=true
azure_ml_job_name=<job-name>
run_id=<run-id>
expected_output_prefix=<storage-prefix>
azure_ml_job_status=Completed
```

## Ubicar Resultados

Los outputs quedan particionados por ambiente, compute, trigger, owner y run id:

```text
<container>/environment=<env>/compute=azure-ml/trigger=batch-endpoint/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/
```

Contenedores funcionales:

- `runs`: summaries, payload de notificacion y `model_run_log.json`.
- `snapshots`: baseline y current history snapshots.
- `drift-logs`: logs de drift, validez y nuevos combos.
- `reports`: reportes Markdown para analista.
- `artifacts`: manifest de artefactos.

Descargar resumen:

```bash
PREFIX="environment=staging/compute=azure-ml/trigger=batch-endpoint/owner=team46/run_date=${RUN_ID:0:8}/run_id=${RUN_ID}"

az storage blob download \
  --account-name "$AZURE_STORAGE_ACCOUNT" \
  --auth-mode login \
  --container-name runs \
  --name "$PREFIX/summaries/run_readiness_summary.csv" \
  --file /tmp/run_readiness_summary.csv \
  --overwrite true
```
