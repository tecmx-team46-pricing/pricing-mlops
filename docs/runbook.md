# Runbook

## Proposito

Operar el flujo Pricing MLOps sin GitHub Actions:

```text
Azure Function -> Azure ML command job -> Storage outputs
```

## Preflight

```bash
az login
az account set --subscription "<azure-subscription-name>"
```

Configurar variables:

```bash
export AZURE_FUNCTION_APP=func-pricing-mlops-staging-<suffix>
export AZURE_RESOURCE_GROUP=rg-pricing-mlops-staging
export AZURE_ML_WORKSPACE=mlw-pricing-mlops-staging-<suffix>
```

## Ejecutar

```bash
scripts/run_model_flow_function.sh staging team46 samples/sample_pricing_v1.csv
```

El script:

- obtiene la Function key sin imprimirla;
- manda `environment`, `run_owner`, `input_blob_path` y `run_id`;
- espera el job AML con ARM/REST;
- verifica metadata de outputs en `runs`, `snapshots`, `drift-logs`, `reports`, `artifacts` y `curated`;
- no imprime dataset ni secretos.

## Seguridad Actual

- `POST /api/model-flow` requiere Function key.
- La Function valida ambiente, owner y blob path.
- Payload maximo: 4096 bytes.
- Errores 500 devuelven mensaje sanitizado y `correlation_id`.
- Azure ML lee/escribe Storage con identidad, no account keys.

Pendiente: mover Function key a Entra ID/Easy Auth o API Management.

## Diagnostico

| Sintoma | Revisar |
|---|---|
| `401` o `403` | Function key, permisos del usuario local para leer keys, Function App correcta. |
| `400` | `environment`, `run_owner` o `input_blob_path` invalido. |
| `413` | Payload demasiado grande. |
| `500` | Usar `correlation_id` y revisar logs de la Function. |
| AML `Failed` | Revisar job en Azure ML Workspace > Jobs. |
| Outputs no encontrados | Confirmar `run_id` y prefix impreso por el script. |
| `az ml` falla localmente | El script no usa `az ml`; usa ARM/REST para esperar el job. |

## Portal

- Function logs: Function App `func-pricing-mlops-staging-<suffix>` > Log stream.
- AML jobs: Workspace `mlw-pricing-mlops-staging-<suffix>` > Jobs.
- Outputs: Storage `<mlops-storage-account>` > Containers.
- Costos: Cost Management > Cost analysis > filtrar `rg-pricing-mlops-staging`.
