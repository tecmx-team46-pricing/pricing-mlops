# pricing-mlops

Repositorio funcional/data science del flujo Pricing MLOps, organizado para mantenerse alineado con Cookiecutter Data Science. Contiene validacion de datos, curated/features, scoring controlado, drift basico, scripts del flujo ML y tests.

Este repo no crea infraestructura Azure ni contiene el runtime de Azure Functions/Azure ML. Consume la plataforma definida en `pricing-mlops-platform`, que ahora es dueña de la orquestacion MLOps bajo `mlops/`.

El flujo actual se identifica como `pricing-baseline-flow`. Es un baseline operativo controlado para validar contrato, orquestacion, trazabilidad y storage layout; no es el modelo productivo definitivo.

## Flujo Actual

```text
raw-masked/samples/sample_pricing_v1.csv
-> Azure Function /api/model-flow
-> Azure ML pipeline/job
-> snapshot de este repo
-> validacion / curated / scoring / drift / report
-> Storage outputs versionados
```

El flujo automatico lo dispara plataforma con Event Grid sobre `raw-masked/incoming/*.csv`. Este repo no contiene Event Grid, Function App ni IaC.

GitHub Actions no es requerido para operar el flujo. Solo se usa para CI y pruebas controladas.

## Instalacion

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Validacion Local

```bash
python -m compileall src scripts tests
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

cd ../pricing-mlops-platform

MODEL_REPO_PATH=../pricing-mlops \
mlops/scripts/publish_orchestrator_function.sh staging

AZURE_FUNCTION_APP=func-pricing-mlops-staging-<suffix> \
AZURE_RESOURCE_GROUP=rg-pricing-mlops-staging \
AZURE_ML_WORKSPACE=mlw-pricing-mlops-stg-v2-<suffix> \
mlops/scripts/run_model_flow_function.sh staging team46 samples/sample_pricing_v1.csv
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
| `workflow_dispatch`, `run_azure_flow=true` | Hace checkout de `pricing-mlops-platform` y llama `pricing-mlops-platform/mlops/scripts/run_model_flow_function.sh`. | Si |

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
<container>/environment=<env>/compute=azure-ml/trigger=<manual|event-grid>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/<artifact>
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

Estos outputs funcionales se escriben solo en el Storage MLOps publicado por plataforma (`AZURE_STORAGE_ACCOUNT`, hoy `<mlops-storage-account>` en `staging`). Azure ML crea snapshots de codigo, logs, environments y artifacts runtime en el Storage runtime del workspace activo; este repo no los interpreta como outputs del modelo.

## Documentacion

- [`docs/runbook.md`](docs/runbook.md)
- [`docs/platform-contract.md`](docs/platform-contract.md)
- [`docs/compute-target-contract.md`](docs/compute-target-contract.md)
- [`docs/data-governance.md`](docs/data-governance.md)

## Limites

- No datos reales ni unmasked en Git.
- No account keys ni connection strings.
- No infraestructura desde este repo.
- No runtime Azure Functions ni YAML de command job AML en este repo; viven en `pricing-mlops-platform/mlops/`.
- No scripts de publicacion u operacion de Azure Function en este repo; usar `pricing-mlops-platform/mlops/scripts/`.
- No Container Apps/Docker como ruta activa.
- No scoring/drift pesado dentro de Azure Function.
