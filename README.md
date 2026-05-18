# pricing-mlops

Repositorio funcional del flujo Pricing MLOps. Contiene validacion de datos, curated/features, scoring controlado, drift basico, Azure Function orchestrator, scripts operativos y tests.

Este repo no crea infraestructura Azure. Consume la plataforma definida en `pricing-mlops-platform`.

## Flujo Actual

```text
raw-masked/samples/sample_pricing_v1.csv
-> Azure Function /api/model-flow
-> Azure ML command job
-> validacion / curated / scoring / drift / report
-> Storage outputs versionados
```

GitHub Actions no es requerido para operar el flujo. Solo se usa para CI y pruebas controladas.

## Instalacion

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Validacion Local

```bash
python -m compileall src scripts tests function_app.py
python -m pytest
python scripts/validate_inputs.py --input data/samples/masked/sample_pricing.csv
python scripts/run_local_flow.py --input data/samples/masked/sample_pricing.csv --output runs/local
```

El flow local escribe en `runs/local/<run_id>/`:

- `model_run_log.json`
- `curated_pricing.csv`
- `model_output_snapshot.csv`
- `model_drift_log.json`
- `report.md`

`runs/` esta ignorado por Git.

## Operacion Sin GitHub Actions

```bash
az login
az account set --subscription "<azure-subscription-name>"

AZURE_FUNCTION_APP=func-pricing-mlops-staging-<suffix> \
AZURE_RESOURCE_GROUP=rg-pricing-mlops-staging \
AZURE_ML_WORKSPACE=mlw-pricing-mlops-staging-<suffix> \
scripts/run_model_flow_function.sh staging team46 samples/sample_pricing_v1.csv
```

El script:

- obtiene la Function key sin imprimirla;
- llama `POST /api/model-flow` usando header `x-functions-key`;
- espera el job Azure ML con ARM/REST, sin `az ml`;
- verifica metadata de los seis outputs en Storage;
- falla si existe `raw-unmasked` en `staging`.

## GitHub Actions

`.github/workflows/model-flow.yml` hace:

| Trigger | Accion | Azure login |
|---|---|---|
| `pull_request` | Compile, tests, validacion sample y flow local. | No |
| `workflow_dispatch`, `run_azure_flow=false` | Misma validacion local. | No |
| `workflow_dispatch`, `run_azure_flow=true` | Llama la Azure Function mediante `scripts/run_model_flow_function.sh`. | Si |

Ambientes permitidos: `staging`, `validation`. No se aceptan sandboxes ni prod.

## Variables Azure Esperadas

Configurar en GitHub environment o exportar localmente:

```text
AZURE_CLIENT_ID
AZURE_TENANT_ID
AZURE_SUBSCRIPTION_ID
AZURE_STORAGE_ACCOUNT
AZURE_RESOURCE_GROUP
AZURE_ML_WORKSPACE
AZURE_FUNCTION_APP
MLOPS_CONTAINER_RAW_MASKED=raw-masked
MLOPS_CONTAINER_CURATED=curated
MLOPS_CONTAINER_RUNS=runs
MLOPS_CONTAINER_SNAPSHOTS=snapshots
MLOPS_CONTAINER_DRIFT_LOGS=drift-logs
MLOPS_CONTAINER_REPORTS=reports
MLOPS_CONTAINER_ARTIFACTS=artifacts
```

## Outputs

```text
<container>/environment=<env>/compute=azure-ml/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/<artifact>
```

Artefactos:

| Container | Archivo |
|---|---|
| `runs` | `model_run_log.json` |
| `snapshots` | `model_output_snapshot.csv` |
| `drift-logs` | `model_drift_log.json` |
| `reports` | `report.md` |
| `artifacts` | `curated_pricing.csv` |
| `curated` | `curated_pricing.csv` |

## Documentacion

- [`docs/runbook.md`](docs/runbook.md)
- [`docs/platform-contract.md`](docs/platform-contract.md)
- [`docs/data-governance.md`](docs/data-governance.md)

## Limites

- No datos reales ni unmasked en Git.
- No account keys ni connection strings.
- No infraestructura desde este repo.
- No Container Apps/Docker como ruta activa.
- No scoring/drift pesado dentro de Azure Function.
