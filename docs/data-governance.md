# Data Governance

## Reglas

- No commitear datos unmasked en Git.
- No commitear Parquet, dumps, bases locales ni outputs grandes.
- No guardar secretos, salts, account keys, connection strings ni endpoints sensibles en archivos versionados.
- Versionar solo samples pequeños, sintéticos o masked.

## Samples

`data/samples/masked/sample_pricing.csv` es sintético y sirve para tests, validaciones y CI. No representa datos reales.

`data/samples/unmasked/` existe solo para documentar la zona local prohibida. Su `.gitignore` bloquea todo excepto el propio archivo `.gitignore`.

## Consumo futuro de datos reales

Los datos reales y unmasked deben vivir fuera de Git en Storage/ADLS gobernado por `pricing-mlops-platform`. El repo funcional consume `raw-masked`, `curated` y `baseline` con permisos mínimos, y escribe artefactos hacia `runs`, `snapshots`, `drift-logs`, `reports` y `artifacts`.

El workflow manual de Azure no lee ni escribe `raw-unmasked`. El dataset compartido inicial debe vivir en `raw-masked/samples/sample_pricing_v1.csv`; Azure Function lo lee con managed identity y escribe outputs versionados por `environment`, `owner`, `run_date` y `run_id`.

Los sandboxes personales son local/admin only. GitHub Actions del modelo usa ambientes compartidos como `staging` o `validation` y separa corridas con `MLOPS_RUN_OWNER`.
