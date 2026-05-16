# Platform Contract

## Proposito

Definir como `pricing-mlops` consume la plataforma sin acoplarse a IaC ni crear recursos Azure.

## Inputs esperados de `pricing-mlops-platform`

El repo plataforma publica valores no sensibles por ambiente mediante GitHub environment variables, artifacts operativos o documentacion de outputs:

- `MLOPS_ENVIRONMENT`
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
| `model_output_snapshot.csv` | Snapshot de scoring controlado con precios recomendados. |
| `model_drift_log.json` | Resultado de drift básico o estado `not_evaluated` si no hay baseline. |
| `report.md` | Resumen humano sin datos sensibles. |

En local se escriben bajo `runs/local/<run_id>/`. En Azure, el layout futuro debe mapear esos artefactos a los contenedores `runs`, `snapshots`, `drift-logs`, `reports` y `artifacts`.

## Limites

`pricing-mlops` no crea ni modifica infraestructura. La integracion real con Storage/ADLS debe usar identidades y permisos publicados por `pricing-mlops-platform`.
