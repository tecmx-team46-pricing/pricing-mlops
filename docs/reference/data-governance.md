# Gobierno De Datos

## Reglas

- No commitear datos reales, unmasked, Parquet grandes, dumps locales ni outputs de corridas.
- Versionar solo samples pequenos, sinteticos o masked.
- Limpiar outputs de notebooks antes de commit si contienen datos sensibles o volumen innecesario.
- Subir inputs reales o masked operativos directo a Storage gobernado.
- No usar account keys ni connection strings en scripts, notebooks o docs.

## Directorios

| Ruta | Uso |
|---|---|
| `data/samples/masked/` | samples pequenos para tests y CI |
| `data/inbox/` | staging local ignorado por git |
| `notebooks/eda/source-record/` | notebooks historicos originales |
| `notebooks/eda/auth_recommendation_monitoring_pipeline_abstraction.ipynb` | notebook transicional alineado a abstracciones |
| `reports/` | solo reportes pequenos aprobados para versionar |

## Storage Operativo

El pipeline lee desde:

```text
raw-masked/<input_blob_path>
baseline/<baseline_snapshot_blob_path>
```

El pipeline publica en:

```text
<container>/environment=<env>/compute=azure-ml/trigger=batch-endpoint/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/
```

## Notebooks

Los notebooks son referencia metodologica o exploracion controlada. La operacion remota debe ejecutarse como componentes Azure ML versionados.

Cuando una celda se vuelve parte del flujo operativo:

1. mover la logica a `src/pricing/*` o `src/pricing_mlops/*`;
2. agregar tests;
3. crear wrapper en `scripts/components/*`;
4. declarar YAML en `azureml/components/*`;
5. registrar assets y correr pipeline.
