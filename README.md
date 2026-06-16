# pricing-mlops

Repositorio funcional y operacional del flujo Pricing MLOps AUTH monitoring. Este repo contiene la logica data science, los componentes Azure ML, el pipeline component, el batch endpoint/deployment y los scripts para registrar, desplegar e invocar el flujo.

`pricing-mlops-platform` queda como base Azure: Resource Groups, Storage, Azure ML Workspace, identidades, RBAC y documentacion de plataforma. Este repo no crea infraestructura base.

## Flujo Actual

```text
Azure ML batch endpoint pricing-auth-monitoring/blue
-> pricing_mlops_auth_monitoring_pipeline:0.1.4
-> validate_prepare
-> build_monitoring_inputs
-> calculate_recommendation_validity
-> calculate_auth_history_drift
-> calculate_operational_decision
-> pricing_mlops_publish_outputs:0.1.2
-> Storage MLOps outputs versionados
```

Componentes Azure ML versionados:

| Componente | Entrypoint | Responsabilidad |
|---|---|---|
| `pricing_mlops_validate_prepare` | `scripts/components/validate_prepare.py` | Descarga el CSV masked, valida y genera curated intermedio. |
| `pricing_mlops_build_monitoring_inputs` | `scripts/components/run_monitoring_step.py --step build_monitoring_inputs` | Prepara snapshots de baseline y current history para monitoreo. |
| `pricing_mlops_calculate_recommendation_validity` | `scripts/components/run_monitoring_step.py --step calculate_recommendation_validity` | Calcula validez de recomendaciones y summaries derivados del notebook. |
| `pricing_mlops_calculate_auth_history_drift` | `scripts/components/run_monitoring_step.py --step calculate_auth_history_drift` | Calcula drift AUTH history contra baseline. |
| `pricing_mlops_calculate_operational_decision` | `scripts/components/run_monitoring_step.py --step calculate_operational_decision` | Produce decision operacional, semaforo y manifest final. |
| `pricing_mlops_publish_outputs` | `scripts/components/publish_outputs.py` | Publica artefactos finales al layout operacional de Storage. |

Los steps de monitoreo se declaran en `src/pricing_mlops/monitoring/pipeline/registry.py` y ejecutan logica reusable de `src/pricing_mlops/monitoring/pipeline/steps/`. Asi Azure ML usa un wrapper comun, pero la logica versionable queda en modulos testeables.

El notebook original queda como referencia del analista. La copia `notebooks/eda/auth_recommendation_monitoring_pipeline_abstraction.ipynb` es transicional para reemplazar logica inline por modulos.

## Instalacion

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Validacion Local

```bash
python -m compileall src scripts tests
python -m pytest
python scripts/validate_inputs.py --input data/samples/masked/sample_pricing.csv
```

## Operacion Azure

Registrar ambiente, componentes y pipeline component:

```bash
AZURE_SUBSCRIPTION_ID=<subscription-id> \
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
scripts/register_azureml_components.sh
```

Crear o actualizar el batch endpoint:

```bash
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
scripts/deploy_auth_monitoring_batch_endpoint.sh
```

Invocar smoke test:

```bash
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
AZURE_STORAGE_ACCOUNT=<storage-account> \
AZURE_ML_JOB_IDENTITY_CLIENT_ID=<client-id> \
scripts/invoke_auth_monitoring_batch_endpoint.sh
```

## Outputs

```text
<container>/environment=<env>/compute=azure-ml/trigger=<trigger>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/<artifact>
```

Artefactos AUTH monitoring esperados:

| Container | Archivo |
|---|---|
| `runs` | `model_run_log.json` y `summaries/*.csv` |
| `snapshots` | `snapshots/*.csv` |
| `drift-logs` | `logs/*.csv` |
| `reports` | `reports/auth_recommendation_validity_report.md` |
| `artifacts` | `manifest/artifact_manifest.json` y entradas auxiliares |

Azure ML puede crear snapshots, environments, logs y artifacts internos en el storage runtime del workspace. Esos blobs no son outputs funcionales del modelo.

## Documentacion

- [`docs/runbook.md`](docs/runbook.md)
- [`docs/auth-monitoring-configuration.md`](docs/auth-monitoring-configuration.md)
- [`docs/platform-contract.md`](docs/platform-contract.md)
- [`docs/compute-target-contract.md`](docs/compute-target-contract.md)
- [`docs/data-governance.md`](docs/data-governance.md)

## Limites

- No datos reales ni unmasked en Git.
- No account keys ni connection strings.
- No Resource Groups, Storage Accounts, Key Vault, Azure ML Workspace ni RBAC base desde este repo.
- No Azure Functions como runtime operacional.
- No ejecutar notebooks completos como runtime operacional principal; Azure ML debe usar componentes versionables.
- No Container Apps/Docker como ruta activa.
