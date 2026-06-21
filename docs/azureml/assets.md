# Azure ML Assets Y Versionado

Los assets Azure ML son la interfaz operacional del repo. Se registran desde `configs/azureml_auth_monitoring.yml`.

## Assets Activos

| Asset | Archivo |
|---|---|
| Environment | `azureml/environment.yml` |
| Componentes | `azureml/components/*.yml` |
| Pipeline component | `azureml/pipelines/auth_monitoring_pipeline.yml` |
| Endpoint | `azureml/endpoints/auth-monitoring-batch-endpoint.yml` |
| Deployment | `azureml/endpoints/auth-monitoring-batch-deployment.yml` |
| Manifest | `azureml/manifests/auth-monitoring-release.json` |

## Componentes Principales

| Componente | Responsabilidad |
|---|---|
| `pricing_mlops_validate_prepare` | valida y prepara input masked/current |
| `pricing_mlops_feature_engineering` | agrega raw transaccional a features AUTH |
| `pricing_mlops_prepare_current_auth_history` | genera `current_auth_history_snapshot_real.csv` |
| `pricing_mlops_build_monitoring_inputs` | normaliza baseline y current para monitoreo |
| `pricing_mlops_calculate_recommendation_validity` | evalua vigencia de recomendaciones |
| `pricing_mlops_calculate_auth_history_drift` | calcula drift AUTH history |
| `pricing_mlops_calculate_operational_decision` | genera semaforo y accion operacional |
| `pricing_mlops_simulate_operational_handoff` | materializa handoff simulado |
| `pricing_mlops_publish_outputs` | publica outputs funcionales en Storage |
| `pricing_mlops_notify_operational_decision` | valida payload de notificacion |

## Reglas De Versionado

- Subir version cuando cambia comportamiento del componente.
- Actualizar el pipeline component cuando cambia el DAG o una version de componente usada.
- Actualizar el manifest cuando el deployment debe apuntar a una nueva version.
- No reutilizar versiones publicadas para comportamientos distintos.

## Registro Manual

```bash
AZURE_SUBSCRIPTION_ID=<subscription-id> \
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
python scripts/azureml/register_assets.py --config configs/azureml_auth_monitoring.yml
```

El script omite componentes ya existentes con la misma version y registra los que faltan.

## Deploy Manual Del Endpoint

```bash
AZURE_SUBSCRIPTION_ID=<subscription-id> \
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
python scripts/azureml/deploy_endpoint.py --config configs/azureml_auth_monitoring.yml
```

Si una cuenta o region requiere un endpoint unico, definir:

```bash
export AZURE_ML_BATCH_ENDPOINT=<endpoint-name>
```
