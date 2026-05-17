# Compute Target Contract

## Proposito

Este repo debe ejecutar el mismo core de Pricing MLOps en distintos targets de Azure sin duplicar logica:

- Azure Machine Learning command job como ruta activa.
- Azure Functions como orquestador ligero.
- Azure Container Apps Job solo como PoC anterior/fallback.

Azure Functions orquesta la ruta operativa. GitHub Actions queda para CI/CD, publicacion de Function y pruebas controladas. El scoring, drift y escritura de artefactos deben ocurrir dentro de Azure ML, no en el runner de GitHub ni dentro de la Function.

## Entrypoint comun

El entrypoint activo para Azure ML es:

```bash
python scripts/run_azure_ml_flow.py
```

Ese wrapper fija `MLOPS_COMPUTE_TARGET=azure-ml` y llama al entrypoint reusable:

```bash
python scripts/run_azure_storage_flow.py
```

Ese proceso:

1. Lee `raw-masked/samples/sample_pricing_v1.csv` desde Azure Storage con `DefaultAzureCredential`.
2. Ejecuta validacion, curated, scoring, drift, run log, snapshot y report usando `pricing_mlops.run`.
3. Sube outputs a Storage con Azure SDK.

Parametros equivalentes:

```text
--input-blob-path
--output-root
--environment
--run-owner
--compute-target
```

## Variables comunes

```text
MLOPS_ENVIRONMENT=staging
MLOPS_RUN_OWNER=team46
MLOPS_COMPUTE_TARGET=azure-ml
AZURE_STORAGE_ACCOUNT=<mlops-storage-account>
MLOPS_CONTAINER_RAW_MASKED=raw-masked
MLOPS_INPUT_BLOB_PATH=samples/sample_pricing_v1.csv
MLOPS_CONTAINER_CURATED=curated
MLOPS_CONTAINER_RUNS=runs
MLOPS_CONTAINER_SNAPSHOTS=snapshots
MLOPS_CONTAINER_DRIFT_LOGS=drift-logs
MLOPS_CONTAINER_REPORTS=reports
MLOPS_CONTAINER_ARTIFACTS=artifacts
```

Azure ML usa Entra ID para leer/escribir Storage. Azure Functions usa Managed Identity para iniciar el job AML. El fallback `direct-aml` desde GitHub Actions queda solo para emergencia si la Function no esta disponible.

## Output layout

Cuando `MLOPS_COMPUTE_TARGET` esta definido, los outputs usan:

```text
<container>/environment=<env>/compute=<target>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/<artifact>
```

Si `MLOPS_COMPUTE_TARGET` no esta definido, se conserva el layout previo:

```text
<container>/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/<artifact>
```

## Azure ML Command Job

`azureml/pricing-mlops-job.yml` define el command job minimo. Usa el mismo codigo del repo, environment Python administrado por Azure ML y `identity: user_identity`.

El job no crea infraestructura, no usa Docker propio como ruta activa, no usa account keys y escribe outputs bajo `compute=azure-ml`.

Nota operativa: con serverless AML, `user_identity` permite que el script use `AzureMLOnBehalfOfCredential`. En GitHub esa identidad es la UAMI OIDC del repo modelo; en ejecuciones locales es la identidad Entra del usuario que somete el job. El Storage MLOps principal mantiene account keys deshabilitadas.

El bloqueo inicial `KeyBasedAuthenticationNotPermitted` se resolvio desde `pricing-mlops-platform` configurando el workspace con `systemDatastoresAuthMode=identity`. El ACR asociado de AML requiere `AcrPull` para las identidades de AML porque Azure ML lo usa para imagenes de runtime; eso no reactiva Container Apps/ACR como ruta de compute.

## Azure Functions Orchestrator

`function_app.py` implementa el orquestador ligero:

- `GET /api/health` devuelve estado basico.
- `POST /api/model-flow` valida `environment`, `run_owner` e `input_blob_path`, genera o acepta `run_id`, somete el job AML y devuelve `azure_ml_job_name` con el prefijo esperado de outputs.

No debe contener logica de pricing propia. En `staging`, la Function se despliega en `centralus` y orquesta Azure ML contra Storage/AML en `eastus2`. Si App Service/Functions no tiene quota disponible, el orquestador queda bloqueado por plataforma y GitHub Actions puede someter AML directamente como emergencia sin ejecutar ML.

## Container Apps Job Legacy

`Dockerfile` empaqueta el repo como proceso Python para el PoC anterior. No es la ruta recomendada activa mientras Azure ML sea viable.

## Comparacion justa

Los targets deben usar:

- mismo input masked;
- mismo run owner;
- mismo core Python;
- mismo contrato de outputs;
- Managed Identity;
- sin account keys;
- sin connection strings;
- sin datos unmasked.
