# Runbook

## Ejecutar El Flujo En Azure

```bash
az login
az account set --subscription "<azure-subscription-name>"

AZURE_FUNCTION_APP=func-pricing-mlops-staging-<suffix> \
AZURE_RESOURCE_GROUP=rg-pricing-mlops-staging \
AZURE_ML_WORKSPACE=mlw-pricing-mlops-staging-<suffix> \
scripts/run_model_flow_function.sh staging team46 samples/sample_pricing_v1.csv
```

## Que Hace El Script

1. Valida ambiente, owner, input y subscription.
2. Obtiene la Function key con Azure CLI sin imprimirla.
3. Llama `POST /api/model-flow` con `x-functions-key`.
4. Espera el job AML con ARM/REST.
5. Verifica los outputs en `runs`, `snapshots`, `drift-logs`, `reports`, `artifacts` y `curated`.
6. Verifica que `raw-unmasked` no exista en `staging`.

## Diagnostico

| Sintoma | Revisar |
|---|---|
| `401` o `403` | Function key, permisos para leer keys, Function App correcta. |
| `400` | `environment`, `run_owner` o `input_blob_path` invalido. |
| `413` | Payload demasiado grande. |
| `500` | Usar `correlation_id` y revisar logs de Function. |
| AML `Failed` | Azure ML Workspace > Jobs. |
| Outputs no encontrados | Confirmar `run_id` y prefix impreso por el script. |

## Portal

- Function logs: Function App `func-pricing-mlops-staging-<suffix>` > Log stream.
- AML jobs: Workspace `mlw-pricing-mlops-staging-<suffix>` > Jobs.
- Outputs: Storage `<mlops-storage-account>` > Containers.
- Costos: Cost Management > Cost analysis > filtrar `rg-pricing-mlops-staging`.
