# Platform Contract

## Responsabilidades

`pricing-mlops` implementa el flujo funcional. `pricing-mlops-platform` crea y gobierna Azure.

Este repo no crea Resource Groups, Storage Accounts, RBAC, Key Vault, Azure ML Workspace ni Function App.

## Runtime

Ruta operativa:

```text
scripts/run_model_flow_function.sh
-> Azure Function /api/model-flow
-> Azure ML command job
-> Storage outputs
```

La Function solo orquesta. Azure ML ejecuta validacion, curated/features, scoring, drift y reportes.

## Inputs De Plataforma

```text
AZURE_SUBSCRIPTION_ID
AZURE_TENANT_ID
AZURE_RESOURCE_GROUP
AZURE_STORAGE_ACCOUNT
AZURE_ML_WORKSPACE
AZURE_FUNCTION_APP
MLOPS_CONTAINER_RAW_MASKED
MLOPS_CONTAINER_CURATED
MLOPS_CONTAINER_RUNS
MLOPS_CONTAINER_SNAPSHOTS
MLOPS_CONTAINER_DRIFT_LOGS
MLOPS_CONTAINER_REPORTS
MLOPS_CONTAINER_ARTIFACTS
```

GitHub Actions tambien requiere `AZURE_CLIENT_ID` para OIDC. La operacion local usa el usuario autenticado con `az login`.

## Entrada

El input remoto minimo es:

```text
raw-masked/samples/sample_pricing_v1.csv
```

`raw-unmasked` no es input de este repo.

## Outputs

Cada corrida produce:

| Archivo | Proposito |
|---|---|
| `model_run_log.json` | Metadata de corrida, estado y rutas. |
| `curated_pricing.csv` | Dataset normalizado para scoring. |
| `model_output_snapshot.csv` | Snapshot de recomendaciones. |
| `model_drift_log.json` | Semaforo y metricas de drift. |
| `report.md` | Resumen humano. |

Layout Azure:

```text
<container>/environment=<env>/compute=azure-ml/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/<artifact>
```

## Seguridad

- No account keys ni connection strings.
- No Owner/Contributor de subscription para este repo.
- No sandbox personal en GitHub Actions.
- Function key es control temporal; siguiente iteracion: Entra ID/Easy Auth o API Management.
