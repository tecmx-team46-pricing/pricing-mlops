# pricing-mlops

Repositorio funcional y operacional del flujo Pricing MLOps AUTH monitoring. Este repo contiene la logica data science, los componentes Azure ML, el pipeline component, el batch endpoint/deployment y los scripts para registrar, desplegar e invocar el flujo.

`pricing-mlops-platform` queda como base Azure: Resource Groups, Storage, Azure ML Workspace, identidades, RBAC y documentacion de plataforma. Este repo no crea infraestructura base.

## Flujo Actual

```text
Azure ML batch endpoint pricing-auth-monitoring/blue
-> pricing_mlops_auth_monitoring_pipeline:0.1.18
-> validate_prepare
-> feature_engineering
-> prepare_current_auth_history
-> build_monitoring_inputs
-> calculate_recommendation_validity
-> calculate_auth_history_drift
-> calculate_operational_decision
-> simulate_operational_handoff
-> pricing_mlops_publish_outputs:0.1.6
-> notify_operational_decision
-> Storage MLOps outputs versionados
```

Componentes Azure ML versionados:

| Componente | Entrypoint | Responsabilidad |
|---|---|---|
| `pricing_mlops_validate_prepare` | `scripts/components/validate_prepare.py` | Descarga el CSV masked, valida y genera curated intermedio. |
| `pricing_mlops_build_baseline_snapshot` | `scripts/components/build_baseline_snapshot.py` | Genera `model_output_snapshot.csv` desde una feature table aprobada. Componente opt-in; no forma parte del camino default. |
| `pricing_mlops_feature_engineering` | `scripts/components/feature_engineering.py` | Genera `curated/current_auth_features.csv` y `curated/feature_table.csv` desde datos masked/current. |
| `pricing_mlops_prepare_current_auth_history` | `scripts/components/prepare_current_auth_history.py` | Genera `current_auth_history_snapshot_real.csv` desde features current publicadas. |
| `pricing_mlops_build_monitoring_inputs` | `scripts/components/run_monitoring_step.py --step build_monitoring_inputs` | Prepara snapshots de baseline y current history para monitoreo. |
| `pricing_mlops_calculate_recommendation_validity` | `scripts/components/run_monitoring_step.py --step calculate_recommendation_validity` | Calcula validez de recomendaciones y summaries derivados del notebook. |
| `pricing_mlops_calculate_auth_history_drift` | `scripts/components/run_monitoring_step.py --step calculate_auth_history_drift` | Calcula drift AUTH history contra baseline. |
| `pricing_mlops_calculate_operational_decision` | `scripts/components/run_monitoring_step.py --step calculate_operational_decision` | Produce decision operacional, semaforo y manifest final. |
| `pricing_mlops_simulate_operational_handoff` | `scripts/components/run_monitoring_step.py --step simulate_operational_handoff` | Simula el siguiente handoff operativo segun el semaforo, sin efectos externos. |
| `pricing_mlops_publish_outputs` | `scripts/components/publish_outputs.py` | Publica artefactos finales al layout operacional de Storage. |
| `pricing_mlops_notify_operational_decision` | `scripts/components/notify_operational_decision.py` | Valida y expone el payload de notificacion como nodo visible del pipeline. |

Arquitectura de paquetes:

- `pricing.*` contiene la logica reusable derivada de notebooks y contratos de datos: validacion/curacion de inputs, monitoreo AUTH, feature engineering, baseline snapshots, scoring adapter y contratos de auditoria.
- `pricing_mlops.*` contiene runtime/orquestacion: registry del pipeline, materializacion de artefactos, IO local y layout operacional.
- `scripts/components/*` son wrappers Azure ML delgados: argumentos, descarga/subida y llamada a funciones importables.

Los steps de monitoreo se declaran en `src/pricing_mlops/monitoring/pipeline/registry.py`. Azure ML usa un wrapper comun, los steps runtime viven en `src/pricing_mlops/monitoring/pipeline/steps/`, y las reglas de negocio/notebook se importan desde `pricing.auth_monitoring`.

Los notebooks originales quedan como registro en `notebooks/eda/source-record/`. La copia `notebooks/eda/auth_recommendation_monitoring_pipeline_abstraction.ipynb` es transicional para reemplazar logica inline por modulos.

Extensiones controladas ya disponibles fuera del camino default:

- `pricing.scoring.score_recommendations` produce una nueva version de `model_output_snapshot.csv` desde una feature table validada, sin acoplarse a una implementacion unica de modelo.
- `pricing.audit.write_sql_audit_records` materializa filas auditables para `model_run_log`, metadata de snapshots y decisiones operacionales antes de conectar una base SQL real.

Brechas restantes contra el plan original:

- enriquecer feature engineering con catalog bins/versiones cuando exista fuente general aprobada;
- uso default de `pricing_mlops_build_baseline_snapshot` despues de aprobacion de negocio;
- scoring real/modelo campeon y promocion/rollback sobre el adaptador;
- conexion SQL productiva para logs, drift y snapshots;
- notificacion externa real o dashboard operativo.

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
python scripts/azureml/register_assets.py --config configs/azureml_auth_monitoring.yml
```

Crear o actualizar el batch endpoint:

```bash
AZURE_SUBSCRIPTION_ID=<subscription-id> \
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
python scripts/azureml/deploy_endpoint.py --config configs/azureml_auth_monitoring.yml
```

Los wrappers `scripts/register_azureml_components.sh` y `scripts/deploy_auth_monitoring_batch_endpoint.sh` quedan como compatibilidad local; ambos delegan a los scripts Python.

Invocar smoke test:

```bash
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
AZURE_STORAGE_ACCOUNT=<storage-account> \
AZURE_ML_JOB_IDENTITY_CLIENT_ID=<client-id> \
AZURE_ML_WAIT_FOR_COMPLETION=true \
scripts/invoke_auth_monitoring_batch_endpoint.sh
```

GitHub Actions registra componentes y actualiza el batch endpoint. La invocacion smoke se deja como validacion local porque crea un job real de Azure ML y puede tardar varios minutos.

## Outputs

```text
<container>/environment=<env>/compute=azure-ml/trigger=<trigger>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/<artifact>
```

Artefactos AUTH monitoring esperados:

| Container | Archivo |
|---|---|
| `runs` | `model_run_log.json`, `summaries/*.csv`, `summaries/notification_payload.json` y `summaries/simulated_operational_handoff.json` |
| `snapshots` | `snapshots/*.csv` |
| `drift-logs` | `logs/*.csv` |
| `reports` | `reports/auth_recommendation_validity_report.md` y `reports/simulated_operational_handoff.md` |
| `artifacts` | `manifest/artifact_manifest.json` y entradas auxiliares |

`summaries/notification_payload.json` es el contrato estable para integrar notificaciones externas. La primera version solo publica el payload; no envia mensajes a Teams, Slack ni email.
`summaries/simulated_operational_handoff.json` y `reports/simulated_operational_handoff.md` son evidencia placeholder del siguiente paso operativo que se tomaria segun el semaforo.

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
