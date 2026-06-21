# GitHub Actions

Este repo tiene dos workflows principales.

## CI

Archivo: `.github/workflows/ci.yml`

Corre en pull request y manualmente:

```text
python -m pip install -e ".[dev]"
python -m compileall src scripts tests
python -m pytest
python scripts/validate_inputs.py --input data/samples/masked/sample_pricing.csv
```

## Azure ML Components

Archivo: `.github/workflows/azureml-components.yml`

Corre en `push` a `main` cuando cambian:

- `azureml/components/**`
- `azureml/pipelines/**`
- `azureml/endpoints/**`
- `azureml/manifests/**`
- `azureml/environment.yml`
- `azureml/conda.yml`
- `scripts/components/**`
- `scripts/azureml/**`
- `src/pricing/auth_monitoring/**`
- `src/pricing_mlops/monitoring/pipeline/**`
- `configs/azureml_auth_monitoring.yml`

El job usa el environment GitHub `staging`, hace login OIDC con `azure/login`, registra assets y despliega el endpoint.

Variables requeridas en el environment:

```text
AZURE_CLIENT_ID
AZURE_TENANT_ID
AZURE_SUBSCRIPTION_ID
AZURE_RESOURCE_GROUP
AZURE_ML_WORKSPACE
AZURE_STORAGE_ACCOUNT
AZURE_ML_JOB_IDENTITY_CLIENT_ID
```

## Docs / GitHub Pages

Archivo: `.github/workflows/docs.yml`

- En pull request: instala dependencias y corre `mkdocs build --strict`.
- En `push` a `main` o `workflow_dispatch`: sube el artifact y despliega GitHub Pages.

El repo debe tener Pages configurado con source `GitHub Actions`. Si `gh api repos/tecmx-team46-pricing/pricing-mlops/pages` devuelve `404`, activar Pages en Settings antes del primer deploy.

## Que No Hace CI/CD

- No sube datos reales a Storage.
- No invoca smoke tests automaticamente.
- No ejecuta notebooks completos.
- No crea infraestructura base de Azure; eso vive en `pricing-mlops-platform`.
