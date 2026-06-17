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
| `pricing_mlops_build_baseline_snapshot` | `scripts/components/build_baseline_snapshot.py` | `model_output_snapshot.csv` opt-in desde feature table aprobada |
| `pricing_mlops_feature_engineering` | `scripts/components/feature_engineering.py` | `curated/current_auth_features.csv`, `curated/feature_table.csv` |
| `pricing_mlops_prepare_current_auth_history` | `scripts/components/prepare_current_auth_history.py` | `current_auth_history_snapshot_real.csv` |
| `pricing_mlops_build_monitoring_inputs` | `scripts/components/run_monitoring_step.py --step build_monitoring_inputs` | Snapshots normalizados para monitoreo |
| `pricing_mlops_calculate_recommendation_validity` | `scripts/components/run_monitoring_step.py --step calculate_recommendation_validity` | Logs y summaries de validez de recomendacion |
| `pricing_mlops_calculate_auth_history_drift` | `scripts/components/run_monitoring_step.py --step calculate_auth_history_drift` | Drift AUTH history y reporte markdown |
| `pricing_mlops_calculate_operational_decision` | `scripts/components/run_monitoring_step.py --step calculate_operational_decision` | Semaforo operacional y manifest final |
| `pricing_mlops_simulate_operational_handoff` | `scripts/components/run_monitoring_step.py --step simulate_operational_handoff` | Evidencia placeholder del handoff operativo |
| `pricing_mlops_publish_outputs` | `scripts/components/publish_outputs.py` | Blobs finales en Storage MLOps |
| `pricing_mlops_notify_operational_decision` | `scripts/components/notify_operational_decision.py` | Payload de notificacion visible en el DAG |

Los componentes basados en `run_monitoring_step.py` comparten el mismo entrypoint. La diferencia entre ellos vive en `src/pricing_mlops/monitoring/pipeline/registry.py`, que define el slug del step, el componente Azure ML, las carpetas de entrada/salida y los bindings de Storage intermedio. Las reglas derivadas del notebook viven en `pricing.auth_monitoring`; `pricing_mlops` solo materializa esas reglas en el runtime de pipeline.

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

`current_history_container` y `current_history_blob_path` apuntan al CSV masked/current que alimenta
`pricing_mlops_feature_engineering`. Despues, `pricing_mlops_prepare_current_auth_history` consume
`artifacts/component-state/<run_id>/feature_engineering/curated/current_auth_features.csv` y `build_monitoring_inputs` consume el
snapshot normalizado publicado en `artifacts/component-state/<run_id>/current_auth_history/snapshots/current_auth_history_snapshot_real.csv`.

`pricing_mlops_build_baseline_snapshot` queda registrado para generar `model_output_snapshot.csv` desde una
feature table aprobada, pero no se ejecuta en el camino default hasta que exista una decision explicita de
promocion/refresco de baseline.

`storage_account` debe ser el Storage MLOps funcional publicado por platform. El workspace y la identidad de job son recursos base provisionados fuera de este repo.

## Containers Funcionales

El pipeline lee datos masked desde:

```text
raw-masked/<input_blob_path>
```

El pipeline tambien puede leer datos current masked desde:

```text
raw-masked/<current_history_blob_path>
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
