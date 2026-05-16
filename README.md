# pricing-mlops

Repositorio funcional para el flujo de modelo de Pricing MLOps. Contiene validaciones de datos, scoring controlado, drift básico, scripts locales, artefactos de corrida y tests.

## Relacion con otros repos

- `pricing-mlops-platform`: dueño de Azure, IaC, ambientes, Storage/ADLS, Key Vault, RBAC, GitHub Actions de despliegue y operación.
- `pricing-mlops`: dueño de lógica funcional de datos/modelo, validación, scoring, drift, notebooks controlados y artefactos de ejecución.
- `pricing-mlops-eda`: referencia histórica/documental y EDA inicial. No es el repo operativo del modelo.

Este repo no crea infraestructura Azure, no despliega recursos y no guarda datos reales o unmasked en Git.

## Instalacion

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Tests y validacion local

```bash
python -m compileall src scripts tests
python -m pytest
python scripts/validate_inputs.py --input data/samples/masked/sample_pricing.csv
python scripts/run_local_flow.py --input data/samples/masked/sample_pricing.csv --output runs/local
```

El flow local escribe artefactos en `runs/local/<run_id>/`:

- `model_run_log.json`
- `model_output_snapshot.csv`
- `model_drift_log.json`
- `report.md`

`runs/` esta ignorado por Git.

## Smoke test manual contra sandbox-local

Copiar `configs/environments/sandbox-local.example.env` a un archivo local no versionado, completar `FUNCTION_HEALTH_ENDPOINT` y exportarlo:

```bash
export FUNCTION_HEALTH_ENDPOINT="https://<function-app>.azurewebsites.net"
python scripts/smoke_health.py
```

Si `FUNCTION_HEALTH_ENDPOINT` apunta solo al host, el script llama `/api/health`. Si incluye path, usa el endpoint configurado. No requiere Azure login cuando el endpoint es publico.

## Que no hace este repo

- No crea Resource Groups, Storage Accounts, Key Vault, redes ni role assignments.
- No usa `azure/login` en PR.
- No guarda secretos, connection strings, account keys ni datos unmasked.
- No sustituye el repo plataforma; consume sus variables, rutas y contratos.

## Datos

Solo se versionan samples pequeños, sintéticos o masked. Los datos reales/unmasked viven fuera de Git en Storage/ADLS gobernado por `pricing-mlops-platform`.

## Convenciones tomadas de Cookiecutter Data Science

Este repo adopta solo las partes útiles para el caso operativo:

- `notebooks/` para notebooks controlados.
- `references/` para diccionarios y notas no sensibles.
- `reports/` para plantillas o ejemplos sanitizados.
- `src/pricing_mlops/modeling/` para interfaces de inferencia.

No adopta `data/raw`, `data/interim` ni `data/processed` porque el contrato de gobierno exige que los datos reales vivan en Storage/ADLS, no en Git.
