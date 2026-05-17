# Compute Target Contract

## Proposito

Este repo debe ejecutar el mismo core de Pricing MLOps en distintos targets de Azure sin duplicar logica:

- Azure Container Apps Job.
- Azure Functions PoC.

GitHub Actions orquesta. El scoring, drift y escritura de artefactos deben ocurrir dentro del compute target.

## Entrypoint comun

El entrypoint reusable es:

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
MLOPS_COMPUTE_TARGET=functions|container-job
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

Container Apps Job usa user-assigned identity; por eso el contenedor tambien recibe:

```text
AZURE_CLIENT_ID=<AZURE_CONTAINERAPP_JOB_CLIENT_ID>
```

Azure Functions PoC debe usar Managed Identity de la Function App. Si se usa system-assigned identity, no requiere `AZURE_CLIENT_ID` dentro del runtime.

## Output layout

Cuando `MLOPS_COMPUTE_TARGET` esta definido, los outputs usan:

```text
<container>/environment=<env>/compute=<target>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/<artifact>
```

Si `MLOPS_COMPUTE_TARGET` no esta definido, se conserva el layout previo:

```text
<container>/environment=<env>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/<artifact>
```

## Azure Functions PoC

`function_app.py` solo envuelve el mismo entrypoint comun:

- `GET /api/health` devuelve estado basico.
- `POST /api/model-flow` ejecuta `run_azure_storage_flow`.

No debe contener logica de pricing propia. Si App Service/Functions no tiene quota disponible, el PoC se considera bloqueado por plataforma y no debe sustituirse con ejecucion en GitHub runner.

## Container Apps Job

`Dockerfile` empaqueta el repo como proceso Python. El job se inicia con `az containerapp job start`, recibe variables del contrato y escribe los mismos outputs.

## Comparacion justa

Ambos targets deben usar:

- mismo input masked;
- mismo run owner;
- mismo core Python;
- mismo contrato de outputs;
- Managed Identity;
- sin account keys;
- sin connection strings;
- sin datos unmasked.
