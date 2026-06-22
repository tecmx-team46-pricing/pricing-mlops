# Cambios Sobre El Documento Original De Avance 7

Este documento explica por qué la versión actualizada de Avance 7 difiere de la migración histórica del PDF original.

La migración histórica se conserva sin cambios en:

- `docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure.tex`
- `docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure.pdf`

La versión corregida de arquitectura vigente queda en:

- `docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure-actualizado.tex`
- `docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure-actualizado.pdf`

## Resumen De Diferencias

| Tema | Documento original | Documento actualizado | Razón del cambio | Evidencia |
|---|---|---|---|---|
| Runtime operacional | Presenta el flujo como `Azure Function -> Azure ML Pipeline -> Storage/ADLS -> Azure SQL audit`. | Presenta el flujo como `Azure ML batch endpoint -> pipeline component/job -> Storage MLOps -> handoff y registros auditables`. | Azure Function ya no es el runtime operativo vigente. El endpoint de ejecución lo administra Azure ML desde `pricing-mlops`. | `pricing-mlops/README.md`, `pricing-mlops/azureml/endpoints/auth-monitoring-batch-endpoint.yml`, `pricing-mlops-platform/docs/index.md`, `pricing-mlops-platform/docs/architecture/azure-ml.md`. |
| Azure SQL audit | Afirma SQL audit como capa implementada metadata-only. | Lo presenta como auditoría productiva pendiente; hoy existen contratos y registros auditables antes de conectar SQL real. | La plataforma actual declara que SQL audit no está desplegado como capa activa. `pricing-mlops` sólo materializa registros auditables. | `pricing-mlops/README.md`, `pricing-mlops-platform/docs/index.md`, `pricing-mlops-platform/docs/architecture/azure-ml.md`. |
| Pipeline | Resume la ejecución como `validate_prepare`, `score_evaluate`, `publish_outputs`. | Documenta `pricing_mlops_auth_monitoring_pipeline:0.1.18` y sus pasos reales. | El pipeline versionado actual tiene más pasos y ya separa feature engineering, monitoring inputs, drift, decisión operacional, handoff, publicación y notificación. | `pricing-mlops/README.md`, `pricing-mlops/azureml/pipelines/auth_monitoring_pipeline.yml`. |
| Responsabilidad entre repositorios | Mezcla plataforma, orquestación y operación ML como si vivieran en una sola capa. | Separa `pricing-mlops-platform` para IaC/base Azure y `pricing-mlops` para componentes, pipeline, endpoint e invocación. | La arquitectura vigente evita doble ownership y concentra cambios del flujo ML en el repo funcional. | `pricing-mlops-platform/docs/operations/end-to-end-flow.md`, `pricing-mlops-platform/docs/architecture/overview.md`, `pricing-mlops/README.md`. |
| Recursos de infraestructura | Omite o no enfatiza recursos actuales de observabilidad, identidad y runtime AML. | Incluye Key Vault, Log Analytics, Application Insights, Managed Identity para jobs, Storage funcional, Storage runtime AML y compute `cpu-cluster`. | La IaC actual provisiona esos recursos y son parte de la base real del flujo. | `pricing-mlops-platform/infra/foundation/main.bicep`, `pricing-mlops-platform/infra/workloads/pricing-mlops/main.bicep`, `pricing-mlops-platform/infra/workloads/pricing-mlops/modules/azure-ml.bicep`. |
| Ambientes | Recomienda avanzar en staging/validation sin detallar todos los límites vigentes. | Aclara que staging y validation habilitan Azure ML, pero no existe prod ni Private Endpoints, ADF, Azure Functions operativas, SQL audit activo o endpoints online. | La documentación actual fija esos límites para evitar vender el MVP como producción completa. | `pricing-mlops-platform/infra/parameters/staging.bicepparam`, `pricing-mlops-platform/infra/parameters/validation.bicepparam`, `pricing-mlops-platform/docs/index.md`, `pricing-mlops-platform/docs/architecture/overview.md`. |
| Drift y model health | La narrativa puede leerse como monitoreo de salud completo del modelo HB-SVI/S-curve. | Lo define como monitoreo operacional/pre-model basado en drift, coverage, price drift y recommendation validity. | El código actual decide acciones operacionales, pero todavía no mide degradación predictiva completa del HB-SVI/S-curve. | `pricing-mlops/src/pricing/auth_monitoring/rules/operational_decision.py`, `pricing-mlops/README.md`. |
| Costo-beneficio GPU | El ahorro de cómputo se presentaba como beneficio secundario y poco material si las corridas eran cortas. | Se agrega escenario de empresa con retraining mensual en NVIDIA A10 y comparación contra monitoreo en `cpu-cluster`. | Si el modelo se entrena cada mes por calendario, drift evita entrenamientos GPU cuando no hay evidencia suficiente; el ahorro incluye factura cloud o costo de oportunidad interno. | Azure Retail Prices API: `Standard_NV36ads_A10_v5` Linux en `eastus2` a USD 3.20/h y `Standard_DS2_v2` Linux en `eastus2` a USD 0.114/h; `pricing-mlops-platform/infra/workloads/pricing-mlops/modules/azure-ml.bicep`; `pricing-mlops/azureml/pipelines/auth_monitoring_pipeline.yml`. |

## Cambios Aplicados En El LaTeX

- Portada y resumen ejecutivo: se actualizó la solución vigente y se añadió una nota de trazabilidad para distinguir la versión histórica de la versión corregida.
- Sección de resumen: se reemplazó la arquitectura Function/SQL por batch endpoint, pipeline component, Storage MLOps y registros auditables.
- Hallazgos: se actualizó el estado posterior a Avance 6 para describir drift operacional integrado en Azure ML.
- Modelo: se mantuvo HB-SVI/S-curve como enfoque analítico, pero se aclaró que el monitoreo actual es operacional/pre-model.
- Arquitectura: se recreó la figura central en TikZ con los dos repositorios, el batch endpoint, el pipeline component, Storage y auditoría pendiente.
- Tabla operativa: se agregó el pipeline `pricing_mlops_auth_monitoring_pipeline:0.1.18`, sus pasos reales y los límites actuales.
- Costo-beneficio: se sustituyó la idea de SQL audit activo por Storage, handoff y registros auditables con SQL productivo pendiente.
- Costo-beneficio GPU: se añadió el caso de retraining mensual en NVIDIA A10 y una tabla de costo por duración para justificar el valor económico de reentrenar sólo por evidencia.
- Riesgos: se añadió el riesgo de reintroducir orquestación fuera del endpoint y se ajustó mitigación de auditoría.
- Roadmap y cierre: se agregaron model health, auditoría productiva, notificación/dashboard y hardening antes de producción.

## Regla Editorial

La versión actualizada no corrige el PDF histórico en sitio. Mantiene el histórico como evidencia documental y crea una edición separada para representar la arquitectura operativa vigente.
