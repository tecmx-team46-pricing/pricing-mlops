# AUTH Monitoring Configuration

Este flujo usa una configuracion compartida para que el notebook, los componentes locales y el pipeline Azure ML lean los mismos umbrales, columnas y metadatos metodologicos.

## Fuente Oficial

La fuente oficial vive en:

```text
src/pricing/auth_monitoring/auth_monitoring_config.json
```

Ese archivo contiene:

- `project`: nombre del flujo, equipo, ambiente logico, scope AUTH, version de baseline y band catalog.
- `schemas`: versiones metodologicas de los outputs principales.
- `columns`: llaves, columnas candidatas de recomendacion, columnas historicas y bins globales.
- `thresholds`: umbrales de PSI, KS, coverage, new combos y decision operacional.

El loader tipado es:

```python
from pricing.auth_monitoring import load_auth_monitoring_config

config = load_auth_monitoring_config()
```

La funcion devuelve un `AuthMonitoringConfig` inmutable. Los componentes del pipeline deben tratarlo como contrato oficial.

## Boundary De Packages

La separacion esperada es:

```text
pricing.auth_monitoring
  = reglas, configuracion y contratos del dominio AUTH monitoring

pricing_mlops.monitoring.pipeline.steps
  = runtime operacional que lee/escribe carpetas del pipeline

scripts/components
  = entrypoints Azure ML delgados
```

El notebook debe consumir `pricing.auth_monitoring` para calculos y configuracion. Los componentes Azure ML deben consumir `pricing_mlops.monitoring.pipeline.steps`.

No se mantienen wrappers legacy para config, artifact contract, reglas derivadas del notebook ni steps fuera de `pipeline.steps`.

## Uso En Componentes

Los componentes y funciones de dominio reciben `config` como dependencia explicita:

```python
result = calculate_auth_history_drift(
    baseline_auth_history_profile=baseline_rows,
    current_auth_history=current_rows,
    run_id=run_id,
    config=config,
)
```

Esto evita duplicar constantes dentro de cada step. Si cambia un umbral oficial, se modifica `auth_monitoring_config.json` y todas las rutas que cargan la config quedan alineadas.

## Uso En El Notebook

El notebook transicional mantiene dos variables:

```python
PIPELINE_MONITORING_CONFIG = load_auth_monitoring_config()
MONITORING_CONFIG = PIPELINE_MONITORING_CONFIG
```

`PIPELINE_MONITORING_CONFIG` representa la configuracion oficial del pipeline. No se debe mutar.

`MONITORING_CONFIG` es la config activa de la corrida del notebook. Por default apunta a la oficial, pero puede recibir overrides locales para experimentos.

## Overrides Experimentales

Para probar sensibilidad sin cambiar produccion, el notebook usa:

```python
EXPERIMENTAL_THRESHOLDS = {
    "psi_yellow": None,
    "psi_red": None,
    "new_combo_rate_red": None,
}

MONITORING_CONFIG = PIPELINE_MONITORING_CONFIG.with_overrides(
    thresholds=EXPERIMENTAL_THRESHOLDS
)
```

Reglas:

- `None` significa "usa el valor oficial".
- Un numero reemplaza temporalmente el valor solo en esa ejecucion del notebook.
- `with_overrides(...)` devuelve una copia; no modifica `PIPELINE_MONITORING_CONFIG`.
- Keys desconocidas fallan rapido con `KeyError`.
- Para cambiar el pipeline oficialmente, no uses overrides: cambia `auth_monitoring_config.json` y valida tests.

Ejemplo local:

```python
EXPERIMENTAL_THRESHOLDS["psi_yellow"] = 0.15
EXPERIMENTAL_THRESHOLDS["new_combo_rate_red"] = 0.20
```

Eso permite comparar si el semaforo cambia bajo otro perfil de sensibilidad, sin contaminar la config oficial.

## Flujo De Decision

La config activa alimenta:

```text
calculate_recommendation_validity
calculate_auth_history_drift
calculate_operational_decision
```

El semaforo final sale de `calculate_operational_decision`. Por eso cualquier override debe declararse al inicio del notebook, antes de ejecutar celdas de calculo.

## Artefactos

La config no publica artefactos. Solo controla umbrales, columnas y metadatos.

La materializacion local de outputs ocurre con:

```python
materialize_monitoring_outputs(...)
write_artifact_manifest(...)
validate_expected_monitoring_artifacts(...)
```

La publicacion final a Storage, SQL, Azure ML tags u otros sinks pertenece a `pricing-mlops-platform`.

## Checklist Para Cambios

Cuando cambies configuracion oficial:

1. Edita `src/pricing/auth_monitoring/auth_monitoring_config.json`.
2. Si agregas un campo nuevo, actualiza `src/pricing/auth_monitoring/config.py`.
3. Agrega o ajusta tests en `tests/test_auth_monitoring_contract.py`.
4. Corre:

```bash
python -m compileall src scripts tests
python -m pytest
```

Cuando solo quieras experimentar en el notebook:

1. Cambia `EXPERIMENTAL_THRESHOLDS`.
2. Ejecuta el notebook desde arriba.
3. Revisa `ACTIVE_EXPERIMENTAL_THRESHOLDS` en la salida de configuracion.
4. No modifiques `auth_monitoring_config.json`.
