# Runbook Operativo

## Validacion Local

```bash
python -m compileall src scripts tests
python -m pytest
python scripts/validate_inputs.py --input data/samples/masked/sample_pricing.csv
```

## Registrar Assets

```bash
AZURE_SUBSCRIPTION_ID=<subscription-id> \
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
python scripts/azureml/register_assets.py --config configs/azureml_auth_monitoring.yml
```

## Desplegar Endpoint

```bash
AZURE_SUBSCRIPTION_ID=<subscription-id> \
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
python scripts/azureml/deploy_endpoint.py --config configs/azureml_auth_monitoring.yml
```

El endpoint default es `pricing-auth-monitoring/blue`. Si una cuenta usa otro nombre, definir `AZURE_ML_BATCH_ENDPOINT`.

## Invocar Corrida

```bash
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
AZURE_STORAGE_ACCOUNT=<storage-account> \
AZURE_ML_JOB_IDENTITY_CLIENT_ID=<client-id> \
AZURE_ML_WAIT_FOR_COMPLETION=true \
scripts/invoke_auth_monitoring_batch_endpoint.sh
```

## Revisar Job

```bash
az ml job show \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --workspace-name "$AZURE_ML_WORKSPACE" \
  --name <azure_ml_job_name> \
  --query "{name:name,status:status,studio:services.Studio.endpoint}" \
  -o json
```

## Revisar Artefactos

```bash
for container in runs snapshots drift-logs reports artifacts; do
  az storage blob list \
    --account-name "$AZURE_STORAGE_ACCOUNT" \
    --auth-mode login \
    --container-name "$container" \
    --prefix "$EXPECTED_OUTPUT_PREFIX" \
    --query "length(@)" \
    -o tsv
done
```

## Leer Summary

```bash
az storage blob download \
  --account-name "$AZURE_STORAGE_ACCOUNT" \
  --auth-mode login \
  --container-name runs \
  --name "$EXPECTED_OUTPUT_PREFIX/summaries/run_readiness_summary.csv" \
  --file /tmp/run_readiness_summary.csv \
  --overwrite true
```

Campos minimos:

```text
run_readiness_status
recommended_operational_action
recommendation_validity_global_status
auth_history_drift_status
new_combo_count
```

## Fallas Comunes

| Sintoma | Revision |
|---|---|
| `ResourceNotFound` endpoint | revisar `AZURE_ML_BATCH_ENDPOINT` y workspace |
| Storage permission denied | revisar managed identity y RBAC `Storage Blob Data Contributor` |
| Key Vault forbidden al construir imagen | revisar permisos Key Vault de la identidad AML |
| compute no tiene identity | revisar `cpu-cluster` y user-assigned identity |
| job queda failed en primer step | descargar logs del child job con `az ml job download` |
