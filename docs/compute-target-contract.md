# Compute Target Contract

## Azure ML

La ruta remota activa es:

```text
Azure Function -> Azure ML command job -> Storage MLOps outputs
```

El job usa `azureml/pricing-mlops-job.yml` y ejecuta `scripts/run_azure_ml_flow.py`. La Function inyecta estos inputs:

```text
storage_account
environment
run_owner
run_id
input_blob_path
```

`storage_account` debe ser el Storage MLOps funcional publicado por plataforma. En `staging` es `<mlops-storage-account>`.

La identidad de metadata del flujo es `pricing-baseline-flow/0.1.0` con `logic_version=controlled-pricing-baseline-v1`. Es baseline operativo, no modelo productivo definitivo.

## Containers Funcionales

El modelo solo lee datos masked desde:

```text
raw-masked/<input_blob_path>
```

El modelo escribe outputs funcionales en:

```text
curated
runs
snapshots
drift-logs
reports
artifacts
```

Cada ruta usa:

```text
environment=<env>/compute=azure-ml/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/
```

## Artifacts Internos Azure ML

Azure ML puede crear artifacts internos de runtime:

```text
azureml
azureml-environments
azureml-blobstore-*
snapshotzips
revisions
aml-environment-image-build
```

Esos artifacts pertenecen al workspace/runtime de Azure ML, no al contrato funcional de `pricing-mlops`. No deben usarse como fuente de datos, outputs de negocio ni evidencia funcional del modelo.

## Seguridad

- No usar account keys ni connection strings para datos MLOps.
- No usar `raw-unmasked`.
- No asumir que el Storage runtime de Azure ML y el Storage MLOps son la misma cuenta.
- GitHub Actions no es requerido para operar el flujo.
