# pricing-mlops

Repositorio funcional para el flujo de modelo de Pricing MLOps. Contiene validaciones de datos, scoring controlado, drift básico, scripts locales, artefactos de corrida y tests.

## Relacion con otros repos

- `pricing-mlops-platform`: dueño de Azure, IaC, ambientes, Storage/ADLS, Key Vault, RBAC, GitHub Actions de despliegue y operación.
- `pricing-mlops`: dueño de lógica funcional de datos/modelo, validación, scoring, drift, notebooks controlados y artefactos de ejecución.
- `pricing-mlops-eda`: referencia histórica/documental y EDA inicial. No es el repo operativo del modelo.

Este repo no crea infraestructura Azure, no despliega recursos y no guarda datos reales o unmasked en Git.

## Instalacion

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Tests y validacion local

```bash
python -m compileall src scripts tests
python -m pytest
python scripts/validate_inputs.py --input data/samples/masked/sample_pricing.csv
python scripts/run_local_flow.py --input data/samples/masked/sample_pricing.csv --output runs/local
```

El flow local escribe artefactos en `runs/local/<run_id>/`:

- `model_run_log.json`
- `curated_pricing.csv`
- `model_output_snapshot.csv`
- `model_drift_log.json`
- `report.md`

`runs/` esta ignorado por Git.

## Workflow manual contra Azure Storage

El workflow `.github/workflows/model-flow.yml` mantiene los pull requests locales: compila, corre tests, valida el sample y ejecuta el flow local como CI. Solo el job manual `azure-model-flow` usa `azure/login@v2`, y solo cuando `run_azure_flow=true`.

En modo Azure, GitHub Actions no ejecuta scoring/drift como compute principal. GitHub construye una imagen Docker, la publica en Azure Container Registry, inicia un Azure Container Apps Job y verifica outputs. El job lee `raw-masked`, ejecuta validacion/curated/scoring/drift y escribe outputs en Storage.

GitHub environments soportados: `staging` y `validation`. `sandbox-local` no se acepta en GitHub Actions.

Variables no secretas requeridas:

```text
AZURE_CLIENT_ID=<modelGithubActionsClientId publicado por pricing-mlops-platform>
AZURE_TENANT_ID=<tenant id>
AZURE_SUBSCRIPTION_ID=<subscription id>
AZURE_STORAGE_ACCOUNT=stpmlops...
AZURE_STORAGE_DFS_ENDPOINT=https://stpmlops....dfs.core.windows.net
AZURE_RESOURCE_GROUP=rg-pricing-mlops-staging
AZURE_CONTAINER_REGISTRY=acrpmlops...
AZURE_CONTAINERAPP_JOB_NAME=job-pricing-mlops-staging
AZURE_CONTAINERAPP_JOB_IDENTITY=id-pricing-mlops-job-staging-legacy
AZURE_CONTAINERAPP_JOB_CLIENT_ID=<job-managed-identity-client-id>
MLOPS_ENVIRONMENT=staging
MLOPS_RUN_OWNER=team46
MLOPS_COMPUTE_TARGET=container-job
MLOPS_CONTAINER_RAW_MASKED=raw-masked
MLOPS_CONTAINER_CURATED=curated
MLOPS_CONTAINER_RUNS=runs
MLOPS_CONTAINER_SNAPSHOTS=snapshots
MLOPS_CONTAINER_DRIFT_LOGS=drift-logs
MLOPS_CONTAINER_REPORTS=reports
MLOPS_CONTAINER_ARTIFACTS=artifacts
```

Ejecucion:

1. Abrir Actions en `pricing-mlops`.
2. Ejecutar `Model Flow`.
3. Seleccionar `environment=staging` o `validation`.
4. Activar `run_azure_flow=true`.
5. Usar `run_owner=team46` para corridas compartidas o un usuario para particionar outputs.
6. Usar `input_blob_path=samples/sample_pricing_v1.csv` para que el Container Apps Job lea el dataset compartido desde `raw-masked`.

Los outputs los escribe el Container Apps Job con Managed Identity y Azure SDK, sin account keys ni connection strings:

```text
runs/environment=<env>/compute=<target>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/model_run_log.json
curated/environment=<env>/compute=<target>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/curated_pricing.csv
snapshots/environment=<env>/compute=<target>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/model_output_snapshot.csv
drift-logs/environment=<env>/compute=<target>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/model_drift_log.json
reports/environment=<env>/compute=<target>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/report.md
artifacts/environment=<env>/compute=<target>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/curated_pricing.csv
```

Ver [`docs/compute-target-contract.md`](docs/compute-target-contract.md) para la comparacion Functions vs Container Apps Job.

## Que no hace este repo

- No crea Resource Groups, Storage Accounts, Key Vault, redes ni role assignments.
- No usa `azure/login` en PR.
- No opera sandboxes personales desde GitHub Actions.
- No despliega infraestructura desde este repo.
- No ejecuta el compute ML real en el runner de GitHub Actions.
- No guarda secretos, connection strings, account keys ni datos unmasked.
- No sustituye el repo plataforma; consume sus variables, rutas y contratos.

## Datos

Solo se versionan samples pequeños, sintéticos o masked. Los datos reales/unmasked viven fuera de Git en Storage/ADLS gobernado por `pricing-mlops-platform`.

El flujo local simula la ruta real así:

```text
data/samples/masked/sample_pricing.csv
-> curated_pricing.csv
-> model_output_snapshot.csv
-> model_drift_log.json
-> model_run_log.json + report.md
```

## Convenciones tomadas de Cookiecutter Data Science

Este repo adopta solo las partes útiles para el caso operativo:

- `notebooks/` para notebooks controlados.
- `references/` para diccionarios y notas no sensibles.
- `reports/` para plantillas o ejemplos sanitizados.
- `src/pricing_mlops/modeling/` para interfaces de inferencia.

No adopta `data/raw`, `data/interim` ni `data/processed` porque el contrato de gobierno exige que los datos reales vivan en Storage/ADLS, no en Git.
