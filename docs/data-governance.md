# Data Governance

- No commitear datos reales, unmasked, Parquet grandes, dumps locales ni outputs.
- Versionar solo samples pequenos, sinteticos o masked.
- `data/samples/masked/sample_pricing.csv` es sintetico para tests y CI.
- `data/samples/unmasked/` queda bloqueado por `.gitignore`.
- Datos reales viven en Storage/ADLS gobernado por `pricing-mlops-platform`.
- El input Azure normal es `raw-masked/samples/sample_pricing_v1.csv`.
- Este repo no lee ni escribe `raw-unmasked`.
- Outputs se particionan por `environment`, `compute=azure-ml`, `owner`, `run_date` y `run_id`.
