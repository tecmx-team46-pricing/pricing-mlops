# Compute Target Contract

## Azure ML

La ruta remota activa es:

```text
Azure Function -> Azure ML pipeline/job -> Storage MLOps outputs
```

El pipeline activo se define en `pricing-mlops-platform/mlops/azureml/pricing-mlops-pipeline.yml`, con `pricing-mlops-job.yml` como fallback command job. La plataforma empaqueta un snapshot de este repo como `pricing-mlops-source/`.

El pipeline visible se compone de pasos funcionales de este repo y un paso de publicacion de plataforma:

| Componente | Entrypoint | Salida principal |
|---|---|---|
| `validate_prepare` | `scripts/components/validate_prepare.py` | `curated_input.csv`, `validation_metadata.json` |
| `build_monitoring_inputs` | `scripts/components/build_monitoring_inputs.py` | Snapshots normalizados para monitoreo |
| `calculate_recommendation_validity` | `scripts/components/calculate_recommendation_validity.py` | Logs y summaries de validez de recomendacion |
| `calculate_auth_history_drift` | `scripts/components/calculate_auth_history_drift.py` | Drift AUTH history y reporte markdown |
| `calculate_operational_decision` | `scripts/components/calculate_operational_decision.py` | Semaforo operacional y manifest final |
| `platform_publish_outputs` | `pricing-mlops-platform/mlops/components/platform_publish_outputs.py` | Blobs finales en Storage MLOps |

La Function inyecta estos inputs:

```text
storage_account
environment
run_owner
run_id
input_blob_path
trigger_type
model_repo
model_ref
model_commit_sha
baseline_snapshot_container
baseline_snapshot_blob_path
current_history_container
current_history_blob_path
```

`storage_account` debe ser el Storage MLOps funcional publicado por plataforma. En `staging` es `<mlops-storage-account>`.

El workspace Azure ML activo de `staging` es `mlw-pricing-mlops-stg-v2-<suffix>`. Su storage asociado es el Storage runtime AML, separado del Storage MLOps funcional.

La ruta AUTH monitoring usa el contrato de configuracion `src/pricing/auth_monitoring/auth_monitoring_config.json` para umbrales, columnas y versiones metodologicas.

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
environment=<env>/compute=azure-ml/trigger=<manual|event-grid>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/
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
