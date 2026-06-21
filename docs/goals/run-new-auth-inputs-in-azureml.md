# Goal: Correr Datos Nuevos En Azure ML Con Alineacion Minima

## Objetivo

Aterrizar el trabajo minimo necesario para correr los datos nuevos en el pipeline Azure ML
`pricing-auth-monitoring/blue`, sin exigir paridad estricta 1:1 con los notebooks.

La prioridad de este goal es que los datos corran end-to-end en Azure ML, publiquen
resultados verificables en Storage y dejen documentada cualquier diferencia razonable contra
Notebook 4. La comparacion con Notebook 4 es una validacion de razonabilidad, no una
condicion estricta de igualdad exacta para esta primera corrida.

## Alcance

Este documento prepara el goal de implementacion. No ejecuta cambios funcionales por si solo.

Incluido en el goal futuro:

- Ajustar la abstraccion MLOps en `pricing-mlops`.
- Correr los inputs nuevos por el pipeline Azure ML existente.
- Validar que los artefactos finales queden publicados y sean interpretables.
- Documentar brechas explicables contra Notebook 4.

Fuera de alcance para este goal:

- Modificar notebooks originales en `notebooks/eda/source-record/`.
- Exigir paridad exacta de semaforo o metricas contra Notebook 4.
- Cambiar infraestructura base en `pricing-mlops-platform`, salvo que aparezca un bloqueo de permisos o recursos.
- Versionar datos reales o pesados bajo `data/inbox/`.

## Hallazgos Base

Inputs locales inspeccionados:

```text
data/inbox/input6mothback/masked_output_recommendations (2).csv
data/inbox/input_avance4_current/masked_current_auth_dataset.csv
```

Baseline entregado:

- Archivo: `masked_output_recommendations (2).csv`
- Filas: `8314`
- Llaves unicas: `8314`
- Columna de recomendacion usada por Notebook 4: `Balanced`
- Tiene columnas requeridas para baseline: `kpn`, `vpareadescription`, `distysegment`, `P20_PRICE`, `P50_PRICE`, `P85_PRICE`

Current Avance 4:

- Archivo: `masked_current_auth_dataset.csv`
- Filas raw: `254316`
- Combos unicos por `kpn`, `vpareadescription`, `distysegment`: `10068`
- Combos nuevos contra baseline: `1754`
- Trae `rslpriceusd`, no `current_price`

Bloqueo actual:

- `validate_prepare` exige `current_price`.
- Los datos reales traen `rslpriceusd`.
- La curacion ya puede derivar `current_price` desde `rslpriceusd`, pero la validacion falla antes.
- El pipeline actual genera un `current_auth_history_snapshot_real.csv` simplificado, mientras Notebook 4 usa un snapshot preparado mas rico.

## Enfoque De Implementacion Futura

El primer objetivo no es cerrar toda la paridad con Notebook 4. El primer objetivo es lograr una
corrida Azure ML completa y auditable con los datos nuevos.

La implementacion debe:

- Aceptar `rslpriceusd` como fuente valida de precio cuando `current_price` no exista.
- Permitir inputs transaccionales con llaves repetidas antes del agregado por feature engineering.
- Mantener la preparacion actual del pipeline como baseline operativo inicial.
- Registrar claramente que Notebook 4 usa un `current_auth_history_snapshot_real.csv` preparado mas rico.
- Aceptar diferencias moderadas de semaforo o metricas si son explicables por la diferencia de preparacion.

La paridad fina con Notebook 4 queda como fase posterior.

## Tareas Futuras Minimas

1. Proteger datos locales:
   - Agregar `data/inbox/` a `.gitignore`.
   - Confirmar con `git status --short` que ningun CSV real queda versionado.

2. Ajustar validacion:
   - Actualizar `src/pricing/preparation/validation.py`.
   - Aceptar `rslpriceusd` como alias de precio cuando `current_price` no exista.
   - Permitir duplicados de llave para datasets transaccionales.

3. Cubrir regresiones con tests minimos:
   - Input con `rslpriceusd` pasa validacion.
   - Raw transaccional se agrega a combos unicos.
   - Baseline carga `8314` recomendaciones en la corrida real o en una validacion local controlada.
   - Current carga cerca de `10068` combos.
   - El pipeline materializa artefactos requeridos.

4. Ejecutar validacion local:
   - `python -m compileall src scripts tests`
   - `python -m pytest`
   - Dry run local con los inputs de `data/inbox` sin escribir artefactos al repo.

5. Registrar y desplegar componentes si cambia version:
   - `python scripts/azureml/register_assets.py --config configs/azureml_auth_monitoring.yml`
   - `python scripts/azureml/deploy_endpoint.py --config configs/azureml_auth_monitoring.yml`

6. Subir inputs a Storage:
   - Baseline: `masked_output_recommendations (2).csv`
   - Current: `masked_current_auth_dataset.csv`

7. Invocar endpoint:
   - Usar `AZURE_ML_WAIT_FOR_COMPLETION=true`.
   - Capturar `azure_ml_job_name`, `run_id` y `expected_output_prefix`.

8. Validar resultados publicados:
   - Revisar Azure ML job status.
   - Revisar Storage en containers `runs`, `snapshots`, `drift-logs`, `reports` y `artifacts`.
   - Revisar `summaries/run_readiness_summary.csv`.
   - Revisar `summaries/operational_decision_summary.csv`.

## Comandos De Referencia

Registro de assets:

```bash
AZURE_SUBSCRIPTION_ID=<subscription-id> \
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
python scripts/azureml/register_assets.py --config configs/azureml_auth_monitoring.yml
```

Despliegue de endpoint:

```bash
AZURE_SUBSCRIPTION_ID=<subscription-id> \
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
python scripts/azureml/deploy_endpoint.py --config configs/azureml_auth_monitoring.yml
```

Invocacion esperada:

```bash
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
AZURE_STORAGE_ACCOUNT=<storage-account> \
AZURE_ML_JOB_IDENTITY_CLIENT_ID=<client-id> \
AZURE_ML_WAIT_FOR_COMPLETION=true \
MLOPS_BASELINE_SNAPSHOT_CONTAINER=<baseline-container> \
MLOPS_BASELINE_SNAPSHOT_BLOB_PATH=<baseline-blob-path> \
MLOPS_INPUT_BLOB_PATH=<current-raw-blob-path> \
MLOPS_CURRENT_HISTORY_CONTAINER=<current-container> \
MLOPS_CURRENT_AUTH_HISTORY_BLOB_PATH=<current-raw-blob-path> \
scripts/invoke_auth_monitoring_batch_endpoint.sh
```

## Criterios De Aceptacion

La corrida inicial se considera aceptada si:

- El job Azure ML termina en `Completed`.
- Los artefactos requeridos existen en Storage.
- Los conteos principales son razonables:
  - baseline cerca de `8314`;
  - current cerca de `10068`;
  - new combos cerca de `1754`.
- El summary final tiene `run_readiness_status`.
- El summary final tiene `recommended_operational_action`.
- Cualquier diferencia contra Notebook 4 queda documentada y no bloquea la corrida si es explicable por la diferencia entre snapshot rico del notebook y snapshot simplificado del pipeline.

## Supuestos

- El goal prioriza ejecucion end-to-end sobre paridad exacta.
- Los notebooks originales no se modifican.
- Las correcciones minimas viven en `pricing-mlops`.
- `pricing-mlops-platform` solo se toca si aparece un bloqueo de permisos, identidad, Storage o Azure ML workspace.
- La paridad fina con Notebook 4 puede quedar como fase posterior.

## Resultado Corrida 2026-06-21

Assets publicados:

- `pricing_mlops_validate_prepare:0.1.5`
- `pricing_mlops_auth_monitoring_pipeline:0.1.18`
- Batch endpoint: `pricing-auth-monitoring/blue`

Inputs subidos a Storage:

- Baseline:
  - Container: `baseline`
  - Blob: `auth-monitoring/input6mothback/masked_output_recommendations_2.csv`
- Current:
  - Container: `raw-masked`
  - Blob: `auth-monitoring/input-avance4-current/masked_current_auth_dataset.csv`

Corrida Azure ML:

- `azure_ml_job_name`: `pipelinejob-383d1962-df20-455e-a30d-648c73a0101d`
- `run_id`: `20260621T025500Z-new-auth-inputs`
- `status`: `Completed`
- `expected_output_prefix`: `environment=staging/compute=azure-ml/trigger=batch-endpoint/owner=team46/run_date=20260621/run_id=20260621T025500Z-new-auth-inputs`

Artefactos publicados:

- `runs`: `8` blobs
- `snapshots`: `3` blobs
- `drift-logs`: `3` blobs
- `reports`: `2` blobs
- `artifacts`: `1` blob bajo el prefijo operacional y `58` blobs bajo `component-state/20260621T025500Z-new-auth-inputs`

Conteos verificados desde artefactos publicados:

- `baseline_recommendation_snapshot.csv`: `8314` filas
- `current_auth_history_snapshot_real.csv`: `10068` filas
- `new_combo_without_baseline_recommendation_log.csv`: `1754` filas
- `run_readiness_summary.csv`:
  - `baseline_recommendation_rows`: `8314`
  - `new_combo_count`: `1754`
  - `run_readiness_status`: `Red`
- `operational_decision_summary.csv`:
  - `recommended_operational_action`: `REVIEW_RED_YELLOW_CASES_AND_RUN_RECOMMENDATION_REFRESH`

Dry run local:

- Tempdir: `/var/folders/_q/ldhs2w893j978t6pmrnsh3740000gn/T/auth_goal_dry_run_1k1mcewl`
- `prepared_rows`: `254316`
- `feature_rows`: `10068`
- `current_history_rows`: `10068`
- `baseline_recommendations`: `8314`
- `new_combo_rows`: `1754`
- `run_readiness_status`: `Red`
- `recommended_operational_action`: `REVIEW_RED_YELLOW_CASES_AND_RUN_RECOMMENDATION_REFRESH`

Diferencia contra Notebook 4:

- La corrida Azure ML usa el snapshot simplificado generado por el pipeline desde el input current raw.
- Notebook 4 usa un `current_auth_history_snapshot_real.csv` preparado mas rico.
- La diferencia en semaforo o metricas no bloquea esta corrida inicial, porque el objetivo aceptado fue ejecucion end-to-end con conteos razonables y artefactos verificables.

Nota operacional:

- `validate_prepare:0.1.3` existia en Azure ML sin output `flow_token`; por eso se publico `validate_prepare:0.1.5`.
- Se agrego `data/inbox/**` a `.amlignore` para evitar subir datos reales al code asset de Azure ML.
