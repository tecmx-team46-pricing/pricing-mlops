# Platform Contract

## Proposito

Definir como `pricing-mlops` consume la plataforma sin acoplarse a IaC ni crear recursos Azure.

## Inputs esperados de `pricing-mlops-platform`

El repo plataforma publica valores no sensibles por ambiente mediante GitHub environment variables, artifacts operativos o documentacion de outputs:

- `MLOPS_ENVIRONMENT`
- `MLOPS_RUN_OWNER`
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_STORAGE_ACCOUNT`
- `AZURE_STORAGE_DFS_ENDPOINT`
- `AZURE_KEY_VAULT_URI`
- `MLOPS_CONTAINER_RAW_MASKED`
- `MLOPS_CONTAINER_CURATED`
- `MLOPS_CONTAINER_BASELINE`
- `MLOPS_CONTAINER_RUNS`
- `MLOPS_CONTAINER_SNAPSHOTS`
- `MLOPS_CONTAINER_DRIFT_LOGS`
- `MLOPS_CONTAINER_REPORTS`
- `MLOPS_CONTAINER_ARTIFACTS`
- `FUNCTION_HEALTH_ENDPOINT`

Los secretos reales, salts, account keys y credenciales viven en Key Vault o en mecanismos gobernados por plataforma. No se versionan.

## Outputs producidos por este repo

Cada corrida local o futura corrida Azure produce un `run_id` y artefactos mínimos:

| Archivo | Proposito |
|---|---|
| `model_run_log.json` | Metadata de corrida, estado, conteos, timestamp y rutas de artefactos. |
| `curated_pricing.csv` | Dataset normalizado para scoring local o futura escritura a `curated`. |
| `model_output_snapshot.csv` | Snapshot de scoring controlado con precios recomendados. |
| `model_drift_log.json` | Resultado de drift básico con métricas estructuradas por variable. |
| `report.md` | Resumen humano sin datos sensibles. |

En local se escriben bajo `runs/local/<run_id>/`. En Azure, el layout futuro debe mapear esos artefactos a los contenedores `curated`, `runs`, `snapshots`, `drift-logs`, `reports` y `artifacts`.

El primer pipeline Azure minimo usa el output `modelGithubActionsClientId` de `pricing-mlops-platform` como `AZURE_CLIENT_ID`. Ese principal solo requiere `Storage Blob Data Contributor` sobre el Storage Account del ambiente compartido, normalmente `staging`. No requiere `Owner`, `Contributor` de subscription ni Key Vault para este paso.

## Layout de subida PoC

```text
runs/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/model_run_log.json
snapshots/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/model_output_snapshot.csv
drift-logs/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/model_drift_log.json
reports/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/report.md
artifacts/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/curated_pricing.csv
```

`input_blob_path`, cuando se use, se resuelve dentro de `MLOPS_CONTAINER_RAW_MASKED`. Si se deja vacio, el workflow usa el sample local sintético/masked y sube solo outputs. `MLOPS_RUN_OWNER` particiona outputs de equipo o usuarios sin crear GitHub environments personales.

## Limites

`pricing-mlops` no crea ni modifica infraestructura. La integracion real con Storage/ADLS debe usar identidades y permisos publicados por `pricing-mlops-platform`.

Los sandboxes personales como `sandbox-local` se usan solo desde local/admin y no son ambientes soportados por el workflow manual.
