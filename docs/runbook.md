# Runbook

## Verificacion Local

```bash
python -m compileall src scripts tests
python -m pytest
python scripts/validate_inputs.py --input data/samples/masked/sample_pricing.csv
```

## Registrar Componentes En Azure ML

```bash
AZURE_SUBSCRIPTION_ID=<subscription-id> \
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
python scripts/azureml/register_assets.py --config configs/azureml_auth_monitoring.yml
```

El script Python registra el environment, command components y `pricing_mlops_auth_monitoring_pipeline` usando `azure-ai-ml`. El wrapper `scripts/register_azureml_components.sh` queda como compatibilidad local y delega al script Python.

## Desplegar Endpoint

```bash
AZURE_SUBSCRIPTION_ID=<subscription-id> \
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
python scripts/azureml/deploy_endpoint.py --config configs/azureml_auth_monitoring.yml
```

El script Python lee `configs/azureml_auth_monitoring.yml`, usa el manifest para seleccionar el pipeline component y crea/actualiza `pricing-auth-monitoring/blue`. El wrapper `scripts/deploy_auth_monitoring_batch_endpoint.sh` queda como compatibilidad local y delega al script Python.

## Invocar Smoke Test

```bash
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
AZURE_STORAGE_ACCOUNT=<storage-account> \
AZURE_ML_JOB_IDENTITY_CLIENT_ID=<client-id> \
AZURE_ML_WAIT_FOR_COMPLETION=true \
scripts/invoke_auth_monitoring_batch_endpoint.sh
```

Este paso no corre en GitHub Actions. GitHub publica el pipeline/endpoint con scripts Python; el smoke se ejecuta localmente cuando se necesita validar el runtime completo de Azure ML.

El resultado imprime:

```text
accepted=true
azure_ml_job_name=<job-name>
run_id=<run-id>
expected_output_prefix=<storage-prefix>
```

## AUTH Monitoring Pipeline

Pasos esperados en Azure ML:

```text
validate_prepare
build_monitoring_inputs
calculate_recommendation_validity
calculate_auth_history_drift
calculate_operational_decision
publish_outputs
```

Inputs obligatorios para una corrida real:

```text
baseline recommendation snapshot path
current AUTH history snapshot path
```

La publicacion final a Storage ocurre en `pricing_mlops_publish_outputs`, dentro de este repo.
