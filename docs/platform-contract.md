# Platform Contract

## Responsabilidades

`pricing-mlops` implementa el flujo funcional/data science. `pricing-mlops-platform` crea y gobierna Azure, y tambien contiene el runtime MLOps de orquestacion bajo `mlops/`.

Este repo no crea Resource Groups, Storage Accounts, RBAC, Key Vault, Azure ML Workspace ni Function App. Tampoco contiene `function_app.py`, `host.json` ni el YAML del pipeline/job AML.

## Runtime

Ruta operativa:

```text
pricing-mlops-platform
-> Azure Function /api/model-flow
-> Azure ML pipeline AUTH monitoring
-> snapshot de este repo
-> Storage outputs
```

La Function solo orquesta. Azure ML ejecuta validacion, preparacion de snapshots, validez de recomendacion, drift AUTH y decision operacional.

Los entrypoints funcionales AUTH monitoring derivados del notebook Avance 4 viven en `scripts/components/`:

- `validate_prepare.py`
- `build_monitoring_inputs.py`
- `calculate_recommendation_validity.py`
- `calculate_auth_history_drift.py`
- `calculate_operational_decision.py`

El pipeline component completo vive en `azureml/pipelines/auth_monitoring_pipeline.yml` y se registra
como `pricing_mlops_auth_monitoring_pipeline:<version>`. Ese pipeline compone los componentes
funcionales de este repo y el componente de publicacion registrado por `pricing-mlops-platform`.

La publicacion final vive en `pricing-mlops-platform/mlops/components/platform_publish_outputs.py`.

La ruta AUTH monitoring no ejecuta el notebook completo; ejecuta componentes versionables y mantiene el notebook como referencia del analista.

## Inputs De Plataforma

Los nombres de recursos Azure, credenciales, variables de ambiente, Function App, Workspace Azure ML y containers finales se definen y validan en `pricing-mlops-platform`.

Este repo solo asume que la plataforma entrega al pipeline los paths y parametros necesarios para ejecutar los componentes funcionales. El Storage MLOps funcional y el Storage runtime interno de Azure ML siguen siendo responsabilidades separadas de plataforma.

## Entrada

El input remoto minimo es:

```text
raw-masked/samples/sample_pricing_v1.csv
```

`raw-unmasked` no es input de este repo.

## Outputs

Cada corrida produce:

| Archivo | Proposito |
|---|---|
| `model_run_log.json` | Metadata de corrida, estado y rutas. |
| `curated_pricing.csv` | Dataset normalizado para scoring. |
| `model_output_snapshot.csv` | Snapshot de recomendaciones. |
| `model_drift_log.json` | Semaforo y metricas de drift. |
| `report.md` | Resumen humano. |

La ruta AUTH monitoring produce, como minimo:

| Archivo | Proposito |
|---|---|
| `snapshots/baseline_recommendation_snapshot.csv` | Baseline usado para evaluar vigencia. |
| `snapshots/current_auth_history_snapshot_real.csv` | Historia AUTH actual evaluada. |
| `logs/auth_recommendation_validity_log.csv` | Resultado por recomendacion. |
| `logs/auth_history_drift_log.csv` | Drift estadistico AUTH. |
| `summaries/operational_decision_summary.csv` | Semaforo y accion operacional. |
| `manifest/artifact_manifest.json` | Manifest del arbol de evidencia. |

Layout Azure:

```text
<container>/environment=<env>/compute=azure-ml/trigger=<manual|event-grid>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/<artifact>
```

Azure ML genera artifacts internos como snapshots de codigo, environments, logs y job artifacts runtime. Esos blobs no son outputs funcionales del modelo y viven en el Storage runtime administrado por plataforma para el workspace activo.

La construccion de metadata, manifest y publicacion final pertenece a plataforma. La logica funcional de este repo produce artefactos locales y manifest neutral; los destinos como Azure Blob, Azure ML y SQL se resuelven fuera de este package.

## Seguridad

- No account keys ni connection strings.
- No Owner/Contributor de subscription para este repo.
- No sandbox personal en pipelines operativos.
- La autenticacion de endpoints operativos pertenece a plataforma.
