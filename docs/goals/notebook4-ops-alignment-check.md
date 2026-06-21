# Goal: Notebook 4 Ops Alignment Check

## Objetivo

Cerrar la revision minima de Ops/MLOps antes de commit/PR para confirmar:

- que `input_baseline_6m_back_current` se usa como baseline/referencia del flujo notebooks 2 al 4;
- que `input_avance4_current` se usa como current para analizar cambio en Notebook 4;
- que cualquier diferencia Notebook 4 vs pipeline queda explicada;
- que no se versionan datos reales ni reportes row-level innecesarios.

## Inputs Confirmados

Interpretacion usada:

- `input_baseline_6m_back_current`: baseline/referencia.
- `input_avance4_current`: current/avance4 para analizar cambio contra baseline.

Esta interpretacion coincide con el mensaje recibido: el baseline viene del flujo Notebook 2 al 4 y `input_avance4` solo entra en Notebook 4 para analizar cambio.

## Que Hace Notebook 4

Fuente inspeccionada:

- `notebooks/eda/source-record/Avance4_Equipo46_AUTH_Recommendation_Validity_Current_History_REAL_v4_operational_decision.ipynb`

Hallazgos relevantes:

- Notebook 4 carga un baseline snapshot desde:
  - `masked_data_inputcomplete_inputauth_output/avance3_outputs/.../snapshots/model_output_snapshot.csv`
- Notebook 4 no usa el raw current directamente para monitoreo.
- Notebook 4 espera un archivo ya preparado:
  - `current_auth_history_snapshot_real.csv`
- El propio notebook indica que ese archivo viene de un notebook limpio de preparacion de datos nuevos:
  - `avance4_new_history_preparation_outputs/.../history/current_auth_history_snapshot_real.csv`
- Notebook 4 usa ese snapshot para construir:
  - `baseline_recommendation_snapshot.csv`
  - `baseline_auth_history_profile.csv`
  - `current_auth_history_snapshot_real.csv`
  - `new_combo_without_baseline_recommendation_log.csv`

## Que Hace El Pipeline Actual

Fuente inspeccionada:

- `src/pricing/features/engineering.py`
- `src/pricing_mlops/monitoring/pipeline/steps/prepare_current_auth_history.py`
- `src/pricing_mlops/monitoring/pipeline/steps/build_monitoring_inputs.py`

Flujo actual:

- `validate_prepare` acepta el raw current y valida llaves/precio.
- `feature_engineering` agrupa el raw current por:
  - `kpn`
  - `vpareadescription`
  - `distysegment`
- `feature_engineering` calcula:
  - `P20_PRICE`
  - `P50_PRICE`
  - `P85_PRICE`
  - `n_transactions`
  - `quantity_sum`
  - `revenue_sum`
- `prepare_current_auth_history` toma esa tabla de features y genera `current_auth_history_snapshot_real.csv`.
- `build_monitoring_inputs` combina baseline y current snapshot para los pasos de monitoreo.

## Brechas Encontradas

### 1. Preparacion current no esta alineada 1:1 con Notebook 4

Clasificacion: `fase posterior de paridad fina`, con un ajuste minimo recomendado antes de usar resultados como decision final de negocio.

Notebook 4 espera un `current_auth_history_snapshot_real.csv` preparado por un notebook previo mas especifico. El pipeline actual genera un snapshot simplificado desde raw current.

Esto no bloquea la corrida end-to-end, pero si bloquea afirmar paridad exacta con Notebook 4.

### 2. `n_transactions` puede quedar degradado en el snapshot final

Clasificacion: `bloqueante antes de afirmar alineacion Notebook 4`.

En la corrida revisada, `current_auth_history_snapshot_real.csv` quedo con `n_transactions = 1` para todos los combos, aunque el input raw tenia muchas filas transaccionales.

La causa probable esta en el flujo:

- `feature_engineering` ya agrega raw rows por combo y calcula `n_transactions`.
- `prepare_current_auth_history` vuelve a agrupar una tabla que ya esta agregada.
- Al volver a agrupar, incrementa `n_transactions` por fila de feature, no preserva el `n_transactions` original de la feature table.

Impacto:

- La corrida Azure ML es valida como prueba end-to-end.
- La interpretacion de metricas de volumen/transacciones debe tomarse con cuidado.
- Antes de pedir visto bueno fuerte de negocio, Ops/MLOps deberia corregir o validar esta preservacion de `n_transactions`.

### 3. Reportes row-level en repo

Clasificacion: `bloqueante antes de commit si se quiere limpiar reportes`.

El repo contenia archivos bajo:

- `reports/auth-monitoring-20260621-new-auth-inputs/`

Estos archivos no son necesarios si solo se va a compartir texto por WhatsApp o un ZIP fuera del repo. En este goal quedaron removidos del working tree para que el commit/PR no incluya reportes row-level.

## Proteccion De Inputs

Verificacion hecha:

- `.gitignore` contiene `data/inbox/**`.
- `.amlignore` contiene `data/inbox/**`.
- `git status --short --ignored data/inbox` muestra:
  - `!! data/inbox/`

Conclusion:

- Los inputs reales estan protegidos para git.
- Los inputs reales tambien quedan fuera del code asset Azure ML.

## Validacion Local Ejecutada

Comando:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/test_validation.py tests/test_azureml_component_specs.py -q
```

Resultado:

```text
12 passed in 0.06s
```

## Recomendacion Ops

Estado recomendado:

- No afirmar todavia que el pipeline esta alineado 1:1 con Notebook 4.
- Si el PR es solo para "pipeline corre end-to-end con los datos nuevos", puede avanzar dejando la brecha documentada.
- Si el PR pretende cerrar alineacion con Notebook 4, falta corregir o validar `prepare_current_auth_history` para preservar correctamente `n_transactions` y cualquier otra preparacion del notebook previo.
- Los reportes row-level `reports/auth-monitoring-20260621-new-auth-inputs/` quedaron removidos del working tree para no llevarlos al commit/PR.

## Texto WhatsApp Sugerido

```text
Esto fue lo que hice:

Use input_baseline_6m_back_current como base/referencia y input_avance4_current como el archivo para revisar el cambio en el notebook 4.

Con eso hice una primera corrida en el pipeline y termino bien.

Lo que encontre es que la corrida ya sirve para validar que el flujo corre de punta a punta, pero todavia estoy revisando una diferencia de preparacion contra Notebook 4. En particular, Notebook 4 usa un archivo current ya preparado antes de comparar, y el pipeline esta generando ese archivo desde el input raw.

Te comparto la salida para que me ayudes a validar si el resultado general hace sentido, pero todavia no lo tomaria como paridad exacta con Notebook 4 hasta cerrar esa diferencia de preparacion.
```
