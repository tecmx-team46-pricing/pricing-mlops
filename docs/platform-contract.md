# Platform Contract

## Responsabilidades

| Repo | Responsabilidad |
|---|---|
| `pricing-mlops-platform` | IaC/base Azure: Resource Groups, Storage, Azure ML Workspace, identidades, RBAC y documentacion de plataforma. |
| `pricing-mlops` | Operacion ML: componentes Azure ML, pipeline component, batch endpoint/deployment, smoke test y publicacion de artefactos. |

Este repo no crea infraestructura base. Si cambia la logica del notebook, componentes, pipeline o endpoint, el cambio vive aqui.

## Runtime

Ruta operativa:

```text
pricing-auth-monitoring/blue
-> pricing_mlops_auth_monitoring_pipeline:<version>
-> pricing_mlops_* command components
-> pricing_mlops_publish_outputs
-> Storage MLOps outputs
```

El pipeline component completo vive en `azureml/pipelines/auth_monitoring_pipeline.yml`. El endpoint/deployment vive en `azureml/endpoints/`. El manifest de release vive en `azureml/manifests/auth-monitoring-release.json`. La lista operativa de assets vive en `configs/azureml_auth_monitoring.yml` y se registra/despliega con scripts Python basados en `azure-ai-ml`.

La ruta default ya materializa la historia AUTH current antes de monitorear:

```text
raw-masked/<current_history_blob_path>
-> pricing_mlops_feature_engineering
-> artifacts/component-state/<run_id>/feature_engineering/curated/current_auth_features.csv
-> pricing_mlops_prepare_current_auth_history
-> artifacts/component-state/<run_id>/current_auth_history/snapshots/current_auth_history_snapshot_real.csv
-> pricing_mlops_build_monitoring_inputs
```

`pricing_mlops_build_baseline_snapshot` existe como componente opt-in para producir `model_output_snapshot.csv` desde una feature table aprobada. No reemplaza automaticamente el baseline activo.

El adaptador `pricing.scoring.score_recommendations` y el escritor `pricing.audit.write_sql_audit_records` quedan disponibles para notebooks y para la siguiente integracion operacional. No invocan modelos externos ni bases SQL productivas sin configuracion explicita.

## Inputs De Plataforma

Platform provee los recursos Azure base y permisos. Este repo recibe nombres de recursos mediante variables o parametros de pipeline:

```text
AZURE_SUBSCRIPTION_ID
AZURE_RESOURCE_GROUP
AZURE_ML_WORKSPACE
AZURE_STORAGE_ACCOUNT
AZURE_ML_JOB_IDENTITY_CLIENT_ID
```

No se usan account keys ni connection strings.

## Outputs

Cada corrida publica evidencia en Storage:

```text
<container>/environment=<env>/compute=azure-ml/trigger=<trigger>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/<artifact>
```

La ruta AUTH monitoring produce, como minimo:

| Archivo | Proposito |
|---|---|
| `model_run_log.json` | Metadata de corrida, estado y rutas. |
| `snapshots/baseline_recommendation_snapshot.csv` | Baseline usado para evaluar vigencia. |
| `snapshots/current_auth_history_snapshot_real.csv` | Historia AUTH actual evaluada. |
| `logs/auth_recommendation_validity_log.csv` | Resultado por recomendacion. |
| `logs/auth_history_drift_log.csv` | Drift estadistico AUTH. |
| `summaries/operational_decision_summary.csv` | Semaforo y accion operacional. |
| `manifest/artifact_manifest.json` | Manifest del arbol de evidencia. |

## Seguridad

- No account keys ni connection strings.
- No Owner/Contributor de subscription para operar el flujo ML.
- No sandbox personal en pipelines operativos.
- El endpoint usa `aad_token`.
