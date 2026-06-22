# Goal: Cubrir diferencias entre Avance 7 y la arquitectura actual

## Objetivo

Crear una versión actualizada del resumen ejecutivo de Avance 7 que conserve el contexto ejecutivo del documento migrado a LaTeX, pero corrija las afirmaciones que ya no coinciden con la infraestructura y operación actuales de `pricing-mlops` y `pricing-mlops-platform`.

El resultado debe dejar explícito que el PDF histórico queda preservado como evidencia documental, mientras que la nueva versión representa la arquitectura operativa vigente.

## Fuente histórica

- PDF original: `/Users/me/Downloads/Avance7_Equipo46_Resumen_Ejecutivo_MLOps_Pricing_Azure_v3.pdf`
- Migración histórica en LaTeX: `docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure.tex`
- PDF histórico versionado: `docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure.pdf`

## Evidencia técnica vigente

Validar contra estas fuentes antes de editar la versión actualizada:

- `pricing-mlops-platform/docs/index.md`
- `pricing-mlops-platform/docs/architecture/azure-ml.md`
- `pricing-mlops-platform/docs/operations/end-to-end-flow.md`
- `pricing-mlops-platform/infra/foundation/main.bicep`
- `pricing-mlops-platform/infra/workloads/pricing-mlops/main.bicep`
- `pricing-mlops-platform/infra/workloads/pricing-mlops/modules/azure-ml.bicep`
- `pricing-mlops-platform/infra/parameters/staging.bicepparam`
- `pricing-mlops-platform/infra/parameters/validation.bicepparam`
- `pricing-mlops/README.md`
- `pricing-mlops/azureml/endpoints/auth-monitoring-batch-endpoint.yml`
- `pricing-mlops/azureml/pipelines/auth_monitoring_pipeline.yml`
- `pricing-mlops/src/pricing/auth_monitoring/rules/operational_decision.py`

## Diferencias que debe cubrir

### 1. Azure Function ya no es runtime operativo

El documento histórico describe el flujo como:

`Azure Function -> Azure ML Pipeline -> Storage/ADLS -> Azure SQL audit`

La versión actualizada debe describir el flujo vigente como:

`Azure ML batch pipeline endpoint -> pipeline component/job -> Storage artifacts -> handoff/audit records`

Debe quedar claro que no existe una Azure Function intermedia operando el runtime productivo.

### 2. Azure SQL audit no está desplegado como capa productiva

La versión actualizada no debe afirmar que Azure SQL audit está implementado como capa productiva. Debe indicar que existen registros auditables y contratos de salida para auditoría, pero la conexión a SQL real sigue pendiente/no desplegada como capa activa.

### 3. El pipeline real tiene más pasos

Reemplazar cualquier narrativa simplificada del pipeline:

`validate_prepare -> score_evaluate -> publish_outputs`

por el pipeline versionado actual:

`pricing_mlops_auth_monitoring_pipeline:0.1.18`

con estos pasos:

- `validate_prepare`
- `feature_engineering`
- `prepare_current_auth_history`
- `build_monitoring_inputs`
- `calculate_recommendation_validity`
- `calculate_auth_history_drift`
- `calculate_operational_decision`
- `simulate_operational_handoff`
- `publish_outputs`
- `notify_operational_decision`

### 4. La responsabilidad está dividida entre dos repositorios

La versión actualizada debe separar responsabilidades:

- `pricing-mlops-platform`: crea base Azure, identidades, RBAC, Storage y Azure ML Workspace.
- `pricing-mlops`: registra componentes, publica el pipeline component, despliega el batch endpoint y ejecuta/invoca el endpoint.

### 5. La infraestructura actual incluye recursos omitidos por el PDF

Agregar al resumen de arquitectura vigente:

- Key Vault.
- Log Analytics.
- Application Insights.
- Managed Identity para jobs.
- Storage funcional.
- Storage runtime de Azure ML.
- Compute `cpu-cluster`.

### 6. Staging/validation están alineados, pero no hay prod

Indicar que `staging` y `validation` tienen `enableAzureMl = true`, pero que la documentación actual declara que no hay:

- ambiente `prod` operativo;
- Private Endpoints;
- ADF operativo;
- Azure Functions operativas;
- Azure SQL audit activo.

### 7. Drift debe presentarse como operacional/pre-model

Mantener la narrativa de drift, coverage, price drift y recommendation validity, pero describirla como monitoreo operacional/pre-model.

No afirmar que ya existe model health completo de HB-SVI/S-curve en producción.

## Archivos esperados

Crear una versión nueva para no alterar el documento histórico:

- `docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure-actualizado.tex`
- `docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure-actualizado.pdf`

Opcional si aporta trazabilidad:

- `docs/project/avance7-architecture-diff.md`

## Plan end-to-end

1. Confirmar que el repo `pricing-mlops` esté limpio o identificar cambios no relacionados.
2. Leer la migración histórica en `docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure.tex`.
3. Leer las fuentes vigentes listadas arriba en `pricing-mlops` y `pricing-mlops-platform`.
4. Crear el `.tex` actualizado copiando la estructura editorial del documento histórico.
5. Reescribir sólo las secciones donde el PDF histórico contradice la arquitectura actual.
6. Actualizar tablas y figuras TikZ para representar el batch endpoint, el pipeline real, la división de responsabilidades y la ausencia de SQL/Functions productivas.
7. Añadir una nota breve de trazabilidad indicando que esta versión corrige la arquitectura vigente y que el documento histórico sigue preservado.
8. Compilar el PDF en `/tmp` con `latexmk`.
9. Revisar visualmente el PDF generado.
10. Copiar el PDF final a `docs/project/` sólo después de que compile y se vea correcto.
11. Verificar que no queden afirmaciones activas incorrectas sobre Azure Function, Azure SQL audit productivo o `score_evaluate`.
12. Ejecutar checks de formato/diff.
13. Dejar el estado listo para commit.

## Comandos de implementación y verificación

Compilar sin ensuciar el repo:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error \
  -output-directory=/tmp/pricing-mlops-avance7-actualizado \
  docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure-actualizado.tex
```

Copiar el PDF final al repo cuando la revisión visual esté aprobada:

```bash
cp /tmp/pricing-mlops-avance7-actualizado/avance7-resumen-ejecutivo-mlops-pricing-azure-actualizado.pdf \
  docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure-actualizado.pdf
```

Inspeccionar paginación:

```bash
pdfinfo /tmp/pricing-mlops-avance7-actualizado/avance7-resumen-ejecutivo-mlops-pricing-azure-actualizado.pdf
```

Buscar afirmaciones legacy que no deben quedar como afirmaciones activas:

```bash
rg -n "Azure Function|Azure SQL audit|score_evaluate|validate_prepare -> score_evaluate" \
  docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure-actualizado.tex
```

Confirmar que la versión actualizada sí mencione los elementos vigentes:

```bash
rg -n "batch endpoint|pricing_mlops_auth_monitoring_pipeline|calculate_auth_history_drift|notify_operational_decision|cpu-cluster|pre-model|operacional" \
  docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure-actualizado.tex
```

Checks finales:

```bash
git diff --check
git status --short docs/project docs/goals
```

## Criterios de aceptación

- El documento histórico y su PDF no se modifican.
- La versión actualizada compila con `xelatex`/`latexmk`.
- El PDF actualizado queda versionado en `docs/project/`.
- La versión actualizada no presenta Azure Function como runtime operativo.
- La versión actualizada no presenta Azure SQL audit como capa productiva desplegada.
- La versión actualizada documenta el pipeline `pricing_mlops_auth_monitoring_pipeline:0.1.18` y sus pasos reales.
- La versión actualizada separa responsabilidades entre `pricing-mlops-platform` y `pricing-mlops`.
- La versión actualizada incluye Key Vault, Log Analytics, Application Insights, Managed Identity, Storage funcional, Storage runtime AML y `cpu-cluster`.
- La versión actualizada aclara que existen `staging` y `validation`, pero no `prod`, Private Endpoints, ADF, Functions operativas ni SQL audit activo.
- Drift queda descrito como monitoreo operacional/pre-model, no como model health completo HB-SVI/S-curve.
- No quedan marcadores de contenido pendiente.

## Notas operativas

- Este goal corrige la narrativa documental; no despliega infraestructura ni cambia código runtime.
- La versión histórica conserva menciones antiguas porque representa el PDF original.
- Si durante la implementación se detectan cambios reales en IaC o pipeline, priorizar la fuente versionada actual sobre este goal y actualizar el goal antes de editar el `.tex`.
