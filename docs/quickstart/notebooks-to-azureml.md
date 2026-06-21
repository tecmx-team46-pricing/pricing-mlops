# Quick Start: Notebook A Azure ML

Este flujo convierte una celda de notebook en una pieza versionable de Azure ML. No se ejecutan notebooks completos como runtime operacional.

## 1. Separar Logica Reusable

Mover la logica de negocio a `src/pricing/*` o `src/pricing_mlops/*`.

- `src/pricing/*`: reglas de dominio, preparacion, scoring, monitoreo AUTH.
- `src/pricing_mlops/*`: orquestacion, IO, registry de steps y materializacion de artefactos.
- `notebooks/eda/source-record/*`: registro historico; no editar como runtime.

Ejemplo:

```python
from pricing.auth_monitoring import load_auth_monitoring_config
from pricing_mlops.monitoring.pipeline.registry import get_step

config = load_auth_monitoring_config()
step = get_step("calculate_auth_history_drift")
```

## 2. Crear Un Wrapper Del Componente

Los entrypoints de Azure ML viven en `scripts/components/`. Deben ser delgados:

- parsear argumentos;
- descargar o leer inputs;
- llamar funciones importables;
- escribir outputs;
- subir artefactos si aplica.

Para steps de monitoreo ya existe un wrapper comun:

```bash
python scripts/components/run_monitoring_step.py --step <step-name> ...
```

## 3. Declarar El Component YAML

Crear o actualizar `azureml/components/<component>.yml`.

Debe incluir:

- `name` versionado;
- `version`;
- `environment`;
- `code`;
- `command`;
- inputs/outputs requeridos.

El command debe usar managed identity cuando lee o escribe Storage:

```text
MLOPS_USE_MANAGED_IDENTITY_CREDENTIAL=true
AZURE_ML_JOB_IDENTITY_CLIENT_ID=${{inputs.job_identity_client_id}}
```

## 4. Conectar El Pipeline

Actualizar `azureml/pipelines/auth_monitoring_pipeline.yml` si el componente debe correr en el DAG default.

Reglas:

- usar `compute: azureml:cpu-cluster`;
- usar `identity: type: managed_identity`;
- pasar `job_identity_client_id`;
- conectar outputs con `flow_token` cuando el paso dependa de otro.

## 5. Registrar Y Probar

Validar local:

```bash
python -m compileall src scripts tests
python -m pytest
```

Registrar assets:

```bash
AZURE_SUBSCRIPTION_ID=<subscription-id> \
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
python scripts/azureml/register_assets.py --config configs/azureml_auth_monitoring.yml
```

Desplegar endpoint:

```bash
AZURE_SUBSCRIPTION_ID=<subscription-id> \
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
python scripts/azureml/deploy_endpoint.py --config configs/azureml_auth_monitoring.yml
```

## 6. Subir Cambios

El workflow `azureml-components` corre en `push` a `main` cuando cambian assets, scripts, config o codigo del pipeline. Ese workflow registra componentes, actualiza el pipeline component y despliega el batch endpoint.

Antes de subir:

```bash
python -m compileall src scripts tests
python -m pytest
git diff --check
```
