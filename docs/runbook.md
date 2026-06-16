# Runbook

## Verificacion Local

Este repo se valida localmente como package funcional:

```bash
python -m compileall src scripts tests
python -m pytest
python scripts/validate_inputs.py --input data/samples/masked/sample_pricing.csv
```

## Operacion Azure

La ejecucion remota del flujo, el diagnostico de Function App, Azure ML, Storage y costos se documenta y opera desde `pricing-mlops-platform`.

Este repo no mantiene runbooks de operacion Azure ni variables de ambiente de plataforma.

## AUTH Monitoring Pipeline

La ruta AUTH monitoring se opera desde `pricing-mlops-platform`. Este repo solo aporta los componentes funcionales y la copia transicional del notebook.

Pasos esperados en Azure ML:

```text
validate_prepare
build_monitoring_inputs
calculate_recommendation_validity
calculate_auth_history_drift
calculate_operational_decision
publish_outputs
```

Inputs obligatorios para una corrida real:

```text
baseline recommendation snapshot path
current AUTH history snapshot path
```

La publicacion final a Storage/SQL/Azure ML pertenece a `pricing-mlops-platform`; los componentes de este repo solo materializan artefactos locales o estado intermedio para el pipeline.
