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

## Smoke test local/admin de sandbox

Los sandboxes personales no se operan desde GitHub Actions. Para pruebas local/admin, copiar `configs/environments/sandbox-local.example.env` a un archivo local no versionado, completar `FUNCTION_HEALTH_ENDPOINT` y exportarlo:

```bash
export FUNCTION_HEALTH_ENDPOINT="https://<function-app>.azurewebsites.net"
python scripts/smoke_health.py
```

Si `FUNCTION_HEALTH_ENDPOINT` apunta solo al host, el script llama `/api/health`. Si incluye path, usa el endpoint configurado. No requiere Azure login cuando el endpoint es publico.

## Workflow manual contra Azure Storage

El workflow `.github/workflows/model-flow.yml` mantiene los pull requests locales: compila, corre tests, valida el sample y ejecuta el flow sin Azure. Solo el job manual `azure-model-flow` usa `azure/login@v2`, y solo cuando `run_azure_flow=true`.

GitHub environments soportados: `staging` y `validation`. `sandbox-local` no se acepta en GitHub Actions.

Variables no secretas requeridas:

```text
AZURE_CLIENT_ID=<modelGithubActionsClientId publicado por pricing-mlops-platform>
AZURE_TENANT_ID=<tenant id>
AZURE_SUBSCRIPTION_ID=<subscription id>
AZURE_STORAGE_ACCOUNT=stpmlops...
AZURE_STORAGE_DFS_ENDPOINT=https://stpmlops....dfs.core.windows.net
MLOPS_ENVIRONMENT=staging
MLOPS_RUN_OWNER=team46
MLOPS_CONTAINER_RAW_MASKED=raw-masked
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
6. Dejar `input_blob_path` vacio para usar `data/samples/masked/sample_pricing.csv`, o indicar un blob bajo `raw-masked` para descargar input desde Storage.

Los outputs se suben con Azure CLI y `--auth-mode login`, sin account keys ni connection strings:

```text
runs/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/model_run_log.json
snapshots/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/model_output_snapshot.csv
drift-logs/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/model_drift_log.json
reports/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/report.md
artifacts/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/curated_pricing.csv
```

## Que no hace este repo

- No crea Resource Groups, Storage Accounts, Key Vault, redes ni role assignments.
- No usa `azure/login` en PR.
- No opera sandboxes personales desde GitHub Actions.
- No despliega infraestructura desde este repo.
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
