# Compute Target Contract

## Azure ML

La ruta remota activa es:

```text
Azure ML batch endpoint
-> pipeline component
-> command components
-> Storage MLOps outputs
```

El pipeline visible se compone de:

| Componente | Entrypoint | Salida principal |
|---|---|---|
| `pricing_mlops_validate_prepare` | `scripts/components/validate_prepare.py` | `curated_input.csv`, `validation_metadata.json` |
| `pricing_mlops_build_monitoring_inputs` | `scripts/components/build_monitoring_inputs.py` | Snapshots normalizados para monitoreo |
| `pricing_mlops_calculate_recommendation_validity` | `scripts/components/calculate_recommendation_validity.py` | Logs y summaries de validez de recomendacion |
| `pricing_mlops_calculate_auth_history_drift` | `scripts/components/calculate_auth_history_drift.py` | Drift AUTH history y reporte markdown |
| `pricing_mlops_calculate_operational_decision` | `scripts/components/calculate_operational_decision.py` | Semaforo operacional y manifest final |
| `pricing_mlops_publish_outputs` | `scripts/components/publish_outputs.py` | Blobs finales en Storage MLOps |

Inputs principales:

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
job_identity_client_id
```

`storage_account` debe ser el Storage MLOps funcional publicado por platform. El workspace y la identidad de job son recursos base provisionados fuera de este repo.

## Containers Funcionales

El pipeline lee datos masked desde:

```text
raw-masked/<input_blob_path>
```

El pipeline publica outputs funcionales en:

```text
curated
runs
snapshots
drift-logs
reports
artifacts
```

## Artifacts Internos Azure ML

Azure ML puede crear artifacts internos de runtime como snapshots, environments, logs y job artifacts. Esos artifacts pertenecen al workspace/runtime de Azure ML, no al contrato funcional de `pricing-mlops`.

## Seguridad

- No usar account keys ni connection strings.
- No usar `raw-unmasked`.
- No asumir que el Storage runtime de Azure ML y el Storage MLOps son la misma cuenta.
- GitHub Actions de este repo puede registrar componentes y actualizar el endpoint usando OIDC/RBAC configurado por platform.
