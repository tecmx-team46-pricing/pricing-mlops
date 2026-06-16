# Platform Contract

## Responsabilidades

`pricing-mlops` implementa el flujo funcional/data science. `pricing-mlops-platform` crea y gobierna Azure, y tambien contiene el runtime MLOps de orquestacion bajo `mlops/`.

Este repo no crea Resource Groups, Storage Accounts, RBAC, Key Vault, Azure ML Workspace ni Function App. Tampoco contiene `function_app.py`, `host.json` ni el YAML del pipeline/job AML.

## Runtime

Ruta operativa:

```text
pricing-mlops-platform/mlops/scripts/run_model_flow_function.sh
-> Azure Function /api/model-flow
-> Azure ML pipeline AUTH monitoring
-> snapshot de este repo
-> Storage outputs
```

La Function solo orquesta. Azure ML ejecuta validacion, preparacion de snapshots, validez de recomendacion, drift AUTH y decision operacional.

Los entrypoints funcionales AUTH monitoring derivados del notebook Avance 4 viven en `scripts/components/`:

- `validate_prepare.py`
- `build_monitoring_inputs.py`
- `calculate_recommendation_validity.py`
- `calculate_auth_history_drift.py`
- `calculate_operational_decision.py`

La publicacion final vive en `pricing-mlops-platform/mlops/components/platform_publish_outputs.py`.

La ruta AUTH monitoring no ejecuta el notebook completo; ejecuta componentes versionables y mantiene el notebook como referencia del analista.

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

`AZURE_STORAGE_ACCOUNT` es el Storage MLOps funcional. No apunta al Storage runtime interno de Azure ML ni al Storage host de Azure Functions.

En `staging`, `AZURE_ML_WORKSPACE` apunta al workspace activo `mlw-pricing-mlops-stg-v2-<suffix>`, cuyo storage asociado es el Storage runtime Azure ML. Los outputs funcionales siguen usando `AZURE_STORAGE_ACCOUNT`.

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

La ruta AUTH monitoring produce, como minimo:

| Archivo | Proposito |
|---|---|
| `snapshots/baseline_recommendation_snapshot.csv` | Baseline usado para evaluar vigencia. |
| `snapshots/current_auth_history_snapshot_real.csv` | Historia AUTH actual evaluada. |
| `logs/auth_recommendation_validity_log.csv` | Resultado por recomendacion. |
| `logs/auth_history_drift_log.csv` | Drift estadistico AUTH. |
| `summaries/operational_decision_summary.csv` | Semaforo y accion operacional. |
| `manifest/artifact_manifest.json` | Manifest del arbol de evidencia. |

Layout Azure:

```text
<container>/environment=<env>/compute=azure-ml/trigger=<manual|event-grid>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/<artifact>
```

Azure ML genera artifacts internos como snapshots de codigo, environments, logs y job artifacts runtime. Esos blobs no son outputs funcionales del modelo y viven en el Storage runtime administrado por plataforma para el workspace activo.

La construccion de metadata, manifest y publicacion esta documentada en
`docs/artifact-publishing-contract.md`. La logica ML produce un `RunResult`
neutral; los destinos como Azure Blob, Azure ML y SQL se resuelven mediante
sinks de infraestructura.

## Seguridad

- No account keys ni connection strings.
- No Owner/Contributor de subscription para este repo.
- No sandbox personal en GitHub Actions.
- Function key es control temporal; siguiente iteracion: Entra ID/Easy Auth o API Management.
