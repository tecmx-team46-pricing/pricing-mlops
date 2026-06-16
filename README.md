# pricing-mlops

Repositorio funcional/data science del flujo Pricing MLOps, organizado para mantenerse alineado con Cookiecutter Data Science. Contiene validacion de datos, preparacion de snapshots, monitoreo AUTH, decision operacional, scripts del flujo ML y tests.

Este repo no crea infraestructura Azure ni contiene el runtime de Azure Functions/Azure ML. Consume la plataforma definida en `pricing-mlops-platform`, que ahora es dueña de la orquestacion MLOps bajo `mlops/`.

El flujo actual se identifica como `auth-monitoring-pipeline`. Es una primera ruta operacional para validar vigencia de recomendaciones AUTH, trazabilidad y storage layout; no es el modelo productivo definitivo.

## Flujo Actual

```text
raw-masked/samples/sample_pricing_v1.csv
-> Azure Function /api/model-flow
-> Azure ML pipeline AUTH monitoring
-> snapshot de este repo
-> validacion / snapshots / validity / drift / operational decision
-> Storage outputs versionados
```

Componentes funcionales expuestos para Azure ML:

| Componente | Entrypoint | Responsabilidad |
|---|---|---|
| `validate_prepare` | `scripts/components/validate_prepare.py` | Descarga el CSV masked, valida y genera curated intermedio. |
| `build_monitoring_inputs` | `scripts/components/build_monitoring_inputs.py` | Prepara snapshots de baseline y current history para monitoreo. |
| `calculate_recommendation_validity` | `scripts/components/calculate_recommendation_validity.py` | Calcula validez de recomendaciones y summaries derivados del notebook. |
| `calculate_auth_history_drift` | `scripts/components/calculate_auth_history_drift.py` | Calcula drift AUTH history contra baseline. |
| `calculate_operational_decision` | `scripts/components/calculate_operational_decision.py` | Produce decision operacional, semaforo y manifest final. |

La publicacion final de esos artefactos a Blob Storage, Azure ML tags o SQL pertenece a `pricing-mlops-platform`.

La ruta AUTH monitoring derivada del notebook usa
`validate_prepare -> build_monitoring_inputs -> calculate_recommendation_validity -> calculate_auth_history_drift -> calculate_operational_decision -> publish_outputs`.
El notebook original queda como referencia del analista y la copia
`notebooks/eda/auth_recommendation_monitoring_pipeline_abstraction.ipynb`
es la version transicional para ir reemplazando logica inline por modulos.

La configuracion oficial de AUTH monitoring vive en
`src/pricing/auth_monitoring/auth_monitoring_config.json`. El notebook puede aplicar overrides
temporales con `EXPERIMENTAL_THRESHOLDS`, pero el pipeline debe consumir la configuracion oficial.
Ver [`docs/auth-monitoring-configuration.md`](docs/auth-monitoring-configuration.md).

La separacion de packages es intencional:

- `pricing.auth_monitoring`: reglas, configuracion y contratos del dominio AUTH monitoring.
- `pricing_mlops.monitoring.pipeline.steps`: runtime operacional que lee/escribe archivos para Azure ML.
- `scripts/components`: entrypoints delgados que parsean argumentos y llaman los steps.

No hay API de compatibilidad bajo `pricing_mlops.monitoring` para reglas, config o artifact contract. Cualquier consumidor debe importar esos elementos desde `pricing.auth_monitoring`.

El flujo automatico lo dispara plataforma con Event Grid sobre `raw-masked/incoming/*.csv`. Este repo no contiene Event Grid, Function App ni IaC.

GitHub Actions en este repo solo se usa para CI funcional. La operacion Azure del flujo vive en `pricing-mlops-platform`.
Los YAMLs bajo `azureml/components/` definen los componentes funcionales versionados que plataforma referencia desde su pipeline; el script `scripts/register_azureml_components.sh` los registra manualmente en el workspace objetivo cuando se promueve una version.

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

Los componentes de monitoreo escriben estado intermedio y artefactos finales bajo los directorios del pipeline:

- `snapshots/`
- `logs/`
- `summaries/`
- `reports/`
- `manifest/`

`runs/` esta ignorado por Git.

## Operacion Azure

La operacion remota se dispara desde `pricing-mlops-platform`. Este repo no publica Function Apps, no ejecuta jobs Azure ML directamente y no mantiene variables de ambiente de plataforma.

## GitHub Actions

`.github/workflows/ci.yml` hace:

| Trigger | Accion |
|---|---|
| `pull_request` | Compile, tests y validacion sample local. |
| `workflow_dispatch` | Misma validacion local ejecutada manualmente. |

## Outputs

```text
<container>/environment=<env>/compute=azure-ml/trigger=<manual|event-grid>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/<artifact>
```

Artefactos:

| Container | Archivo |
|---|---|
| `runs` | `model_run_log.json` |
| `snapshots` | `model_output_snapshot.csv` |
| `drift-logs` | `model_drift_log.json` |
| `reports` | `report.md` |
| `artifacts` | `curated_pricing.csv` |
| `curated` | `curated_pricing.csv` |

Estos outputs funcionales se escriben solo en el Storage MLOps publicado por plataforma. Azure ML crea snapshots de codigo, logs, environments y artifacts runtime en el Storage runtime del workspace activo; este repo no los interpreta como outputs del modelo.

## Metadata Audit

La plataforma puede activar sinks como Azure Blob o SQL metadata. En ese modo este repo sigue generando los mismos artefactos locales y `pricing-mlops-platform` los publica en:

- `dbo.model_run_log`
- `dbo.model_output_snapshot_metadata`

SQL es metadata-only. Los CSVs y reportes siguen en Blob Storage. La conexion y los sinks son responsabilidad de plataforma; este repo no usa account keys ni connection strings.

## Documentacion

- [`docs/runbook.md`](docs/runbook.md)
- [`docs/auth-monitoring-configuration.md`](docs/auth-monitoring-configuration.md)
- [`docs/platform-contract.md`](docs/platform-contract.md)
- [`docs/compute-target-contract.md`](docs/compute-target-contract.md)
- [`docs/data-governance.md`](docs/data-governance.md)

## Limites

- No datos reales ni unmasked en Git.
- No account keys ni connection strings.
- No infraestructura desde este repo.
- No runtime Azure Functions ni YAML de pipeline/job AML en este repo; viven en `pricing-mlops-platform/mlops/`.
- No workflows de operacion Azure; este repo solo versiona specs de componentes AML y un script manual de registro.
- No scripts de publicacion u operacion de Azure Function en este repo; usar `pricing-mlops-platform/mlops/scripts/`.
- No ejecutar notebooks completos como runtime operacional principal; Azure ML debe usar componentes versionables.
- No Container Apps/Docker como ruta activa.
- No scoring/drift pesado dentro de Azure Function.
