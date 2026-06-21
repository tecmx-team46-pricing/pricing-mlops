# Reporte Para Analista: AUTH Monitoring New Inputs

## Resumen

Corrida end-to-end de los inputs nuevos en Azure ML `pricing-auth-monitoring/blue`.
El objetivo fue validar ejecucion operativa y artefactos verificables con alineacion minima contra Notebook 4, sin exigir paridad exacta.

- Azure ML job: `pipelinejob-383d1962-df20-455e-a30d-648c73a0101d`
- Display name: `lucid_fennel_ggxgf5n3`
- Run id: `20260621T025500Z-new-auth-inputs`
- Status: `Completed`
- Studio: <https://ml.azure.com/runs/pipelinejob-383d1962-df20-455e-a30d-648c73a0101d?wsid=/subscriptions/a288ca29-947f-439f-8e5e-436f374b8a39/resourcegroups/rg-pricing-mlops-main/workspaces/mlw-pmlops-06152240&tid=c65a3ea6-0f7c-400b-8934-5a6dc1705645>
- Storage account: `stpmlops06152240`
- Output prefix: `environment=staging/compute=azure-ml/trigger=batch-endpoint/owner=team46/run_date=20260621/run_id=20260621T025500Z-new-auth-inputs`

## Resultado Principal

- Baseline publicado: `8314` recomendaciones.
- Current history publicado: `10068` combos.
- Combos nuevos contra baseline: `1754`.
- `run_readiness_status`: `Red`.
- `recommended_operational_action`: `REVIEW_RED_YELLOW_CASES_AND_RUN_RECOMMENDATION_REFRESH`.

Interpretacion corta: la corrida no fallo. El estado `Red` viene de reglas de monitoreo que detectan riesgo accionable en recomendaciones existentes y sugieren revision/refresh de recomendaciones. La decision tambien indica `NOT_REQUIRED_FROM_PRICE_DRIFT_ALONE` para HB-SVI, asi que no debe leerse como requerimiento automatico de reentrenamiento completo.

## Inputs Usados

| Tipo | Container | Blob |
|---|---|---|
| Baseline | `baseline` | `auth-monitoring/input6mothback/masked_output_recommendations_2.csv` |
| Current | `raw-masked` | `auth-monitoring/input-avance4-current/masked_current_auth_dataset.csv` |

## Archivos Clave Para Revisar

Primero revisar estos archivos:

1. `runs/.../summaries/run_readiness_summary.csv`
   - Contiene `run_readiness_status`, conteos de baseline/new combos y status por dimension.
2. `runs/.../summaries/operational_decision_summary.csv`
   - Contiene `recommended_operational_action` y rationale operacional.
3. `drift-logs/.../logs/auth_recommendation_validity_log.csv`
   - Detalle row-level de semaforo por recomendacion existente.
4. `drift-logs/.../logs/new_combo_without_baseline_recommendation_log.csv`
   - Lista de los `1754` combos nuevos sin recomendacion baseline.
5. `snapshots/.../snapshots/current_auth_history_snapshot_real.csv`
   - Snapshot current simplificado generado por el pipeline.
6. `reports/.../reports/auth_recommendation_validity_report.md`
   - Reporte Markdown resumido generado por el pipeline.

El inventario completo esta en:

- `reports/auth-monitoring-20260621-new-auth-inputs/artifact_inventory.csv`

Para descargar todo el set operacional con Azure CLI:

```bash
bash reports/auth-monitoring-20260621-new-auth-inputs/download_artifacts.sh
```

Por default descarga en:

```text
/tmp/auth-monitoring-20260621-new-auth-inputs
```

## Artefactos Publicados

| Container | Cantidad | Uso |
|---|---:|---|
| `runs` | 8 | Summaries, payloads y log de corrida. |
| `snapshots` | 3 | Baseline recommendation, baseline profile y current history. |
| `drift-logs` | 3 | Logs de validez, drift y combos nuevos. |
| `reports` | 2 | Reportes Markdown generados por pipeline. |
| `artifacts` | 1 | Manifest operacional publicado. |

Tambien existen `58` blobs intermedios bajo:

```text
artifacts/component-state/20260621T025500Z-new-auth-inputs
```

Esos intermedios son utiles para debugging de MLOps, pero para analisis de negocio normalmente basta con los containers operacionales anteriores.

## Conteos Verificados

| Fuente | Conteo |
|---|---:|
| Input current raw | `254316` filas |
| Baseline recommendation snapshot | `8314` filas |
| Current auth history snapshot | `10068` filas |
| New combo log | `1754` filas |
| Validity log | `8314` filas |

## Diferencia Esperada Contra Notebook 4

Notebook 4 usa un `current_auth_history_snapshot_real.csv` preparado mas rico. Esta corrida Azure ML genera el snapshot current desde el input raw usando la abstraccion actual del pipeline. Por eso puede haber diferencias moderadas en semaforo o metricas contra el notebook original.

Para esta corrida inicial, esas diferencias no bloquean: el criterio aceptado fue end-to-end `Completed`, artefactos publicados y conteos razonables.

## Checklist Sugerido Para Analisis

1. Abrir `run_readiness_summary.csv` y confirmar status global y tasas.
2. Abrir `operational_decision_summary.csv` y validar si el rationale hace sentido de negocio.
3. Filtrar `auth_recommendation_validity_log.csv` por casos `Red` y `Yellow`.
4. Revisar `new_combo_without_baseline_recommendation_log.csv` para priorizar los `1754` combos nuevos.
5. Si se compara contra Notebook 4, separar diferencias por preparacion de snapshot vs diferencias de reglas.
6. No usar esta corrida como prueba de paridad exacta Notebook 4; usarla como corrida operativa base.
