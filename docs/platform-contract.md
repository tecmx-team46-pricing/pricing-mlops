# Platform Contract

## Proposito

Definir como `pricing-mlops` consume la plataforma sin acoplarse a IaC ni crear recursos Azure.

## Inputs esperados de `pricing-mlops-platform`

El repo plataforma publica valores no sensibles por ambiente mediante GitHub environment variables, artifacts operativos o documentacion de outputs:

- `MLOPS_ENVIRONMENT`
- `MLOPS_RUN_OWNER`
- `MLOPS_COMPUTE_TARGET`
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_STORAGE_ACCOUNT`
- `AZURE_STORAGE_DFS_ENDPOINT`
- `AZURE_RESOURCE_GROUP`
- `AZURE_ML_WORKSPACE`
- `AZURE_FUNCTION_APP`
- `AZURE_KEY_VAULT_URI`
- `MLOPS_CONTAINER_RAW_MASKED`
- `MLOPS_CONTAINER_CURATED`
- `MLOPS_CONTAINER_BASELINE`
- `MLOPS_CONTAINER_RUNS`
- `MLOPS_CONTAINER_SNAPSHOTS`
- `MLOPS_CONTAINER_DRIFT_LOGS`
- `MLOPS_CONTAINER_REPORTS`
- `MLOPS_CONTAINER_ARTIFACTS`

Los secretos reales, salts, account keys y credenciales viven en Key Vault o en mecanismos gobernados por plataforma. No se versionan.

## Outputs producidos por este repo

Cada corrida local o corrida Azure produce un `run_id` y artefactos mínimos:

| Archivo | Proposito |
|---|---|
| `model_run_log.json` | Metadata de corrida, estado, conteos, timestamp y rutas de artefactos. |
| `curated_pricing.csv` | Dataset normalizado para scoring local o futura escritura a `curated`. |
| `model_output_snapshot.csv` | Snapshot de scoring controlado con precios recomendados. |
| `model_drift_log.json` | Resultado de drift básico con métricas estructuradas por variable. |
| `report.md` | Resumen humano sin datos sensibles. |

En local se escriben bajo `runs/local/<run_id>/`. En Azure, Azure ML escribe esos artefactos a los contenedores `curated`, `runs`, `snapshots`, `drift-logs`, `reports` y `artifacts`.

El pipeline Azure minimo operativo usa Azure Functions como orquestador. La Function valida el request, somete un Azure ML command job y devuelve `azure_ml_job_name`, `run_id`, `correlation_id` y el prefijo esperado de outputs. GitHub Actions puede publicar la Function o llamar el endpoint para pruebas controladas, pero no es requerido para operar el flujo. El fallback `direct-aml` usa el output `modelGithubActionsClientId` de `pricing-mlops-platform` como `AZURE_CLIENT_ID` del runner de GitHub y solo debe usarse si la Function esta bloqueada. No requiere `Owner`, `Contributor` de subscription ni acceso a `raw-unmasked`.

## Layout de subida PoC

```text
runs/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/model_run_log.json
snapshots/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/model_output_snapshot.csv
drift-logs/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/model_drift_log.json
reports/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/report.md
artifacts/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/curated_pricing.csv
curated/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/curated_pricing.csv
```

Para comparar compute targets, si `MLOPS_COMPUTE_TARGET` esta definido, se agrega al path:

```text
runs/environment=<env>/compute=<target>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/model_run_log.json
snapshots/environment=<env>/compute=<target>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/model_output_snapshot.csv
drift-logs/environment=<env>/compute=<target>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/model_drift_log.json
reports/environment=<env>/compute=<target>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/report.md
artifacts/environment=<env>/compute=<target>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/curated_pricing.csv
curated/environment=<env>/compute=<target>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/curated_pricing.csv
```

`input_blob_path` se resuelve dentro de `MLOPS_CONTAINER_RAW_MASKED`. El dataset compartido inicial es `raw-masked/samples/sample_pricing_v1.csv`. `MLOPS_RUN_OWNER` particiona outputs de equipo o usuarios sin crear GitHub environments personales.

## Limites

`pricing-mlops` no crea ni modifica infraestructura. La integracion real con Storage/ADLS debe usar identidades y permisos publicados por `pricing-mlops-platform`.

GitHub Actions no es compute ML ni orquestador operativo principal. La operacion normal es llamar `POST /api/model-flow` en Azure Functions con `scripts/run_model_flow_function.sh`; Azure ML ejecuta validacion, curated, scoring, drift y escritura de artefactos. En `workflow_dispatch`, GitHub Actions puede llamar la Function para pruebas controladas o usar `direct-aml` como fallback de emergencia. La Function key es temporal; la siguiente iteracion debe evaluar Entra ID/Easy Auth o API Management.

Los sandboxes personales como `sandbox-local` se usan solo desde local/admin y no son ambientes soportados por el workflow manual.
