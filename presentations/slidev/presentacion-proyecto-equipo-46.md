---
theme: default
title: "Plataforma MLOps para Pricing Intelligence en Azure"
layout: tec-cover
canvasWidth: 960
colorSchema: light
transition: fade-out
drawings:
  persist: false
mdc: true
railText: Presentación del Proyecto Integrador
program:
  - Maestría en Inteligencia
  - Artificial Aplicada (MNA)
organization: AUTH Monitoring / Pricing
presenters:
  - Emanuel Flores Martinez
  - Mario Javier Soriano Aguilera
  - David Alberto Serrano Garcia
advisor: Por confirmar
sponsor: Mario
date: Junio 2026
coverMedia:
  kind: cover-cycle
  ariaLabel: Retraining por evidencia
  title: Retraining por evidencia
  items:
    - Baseline
    - Drift
    - Decisión
---
---
layout: tec-content
title: Tesis ejecutiva
projectName: Pricing MLOps AUTH Monitoring
ariaLabel: Tesis ejecutiva
media:
  kind: flow
  ariaLabel: Flujo de decisión por evidencia
  items:
    - Datos AUTH recientes
    - Drift operacional
    - Decisión MLOps
content:
  kind: statement-stack
  statement: La decisión central es conservar, actualizar o reentrenar el modelo HB-SVI/S-curve sólo cuando la evidencia operacional lo justifique.
  stack:
    - value: "No"
      label: retraining mensual por rutina
    - value: Sí
      label: coverage, drift, validez y decisión trazable
    - value: Hoy
      label: foundation/MVP en ruta a validation
---
---
layout: tec-content
title: "Parte 1: notebooks a evidencia MLOps"
projectName: Pricing MLOps AUTH Monitoring
ariaLabel: Parte 1
media:
  kind: timeline
  ariaLabel: Avances analíticos
  items:
    - value: Avance 1
      label: EDA
    - value: Avance 2
      label: Features
    - value: Avance 3
      label: Baseline
    - value: Avance 4
      label: Drift AUTH
content:
  kind: section-intro
  label: Objetivo de esta mitad
  text: "Convertir exploración de notebooks en evidencia medible: calidad, features, baseline, drift y decisión operacional."
  tags:
    - Datos masked
    - Contratos de columnas
    - Artefactos versionables
    - AUTH-only scope
---
---
layout: tec-content
title: EDA + feature engineering
projectName: Pricing MLOps AUTH Monitoring
ariaLabel: EDA y feature engineering
media:
  kind: metric-strip
  ariaLabel: Hallazgos de preparación
  items:
    - value: "~234k"
      label: filas masked de entrada
    - value: Nulos
      label: estructurales
    - value: "8,314"
      label: filas de feature table
    - value: P20-P85
      label: bandas de monitoreo
content:
  kind: two-column
  columns:
    - title: Lo que se resolvió
      bullets:
        - Perfilar long-tail de precio/cantidad sin tratarlo como error automático.
        - Separar nulos estructurales de fallas reales de origen.
        - Construir features de demanda, precio, margen, bins, cobertura y llaves técnicas.
    - title: Implicación MLOps
      variant: muted
      text: La feature table se vuelve contrato entre notebooks, componentes Azure ML, baseline y monitoreo AUTH.
---
---
layout: tec-content
title: Baseline de recomendaciones
projectName: Pricing MLOps AUTH Monitoring
ariaLabel: Baseline MLOps
media:
  kind: status-band
  ariaLabel: Semáforo baseline
  items:
    - status: green
      label: Green 61.58%
    - status: yellow
      label: Yellow 38.42%
    - status: red
      label: Red 0%
content:
  kind: kpi-grid
  items:
    - value: "8,314"
      label: recomendaciones congeladas
    - value: "6,982"
      label: KPN representados
    - value: 0%
      label: casos Red en baseline
    - value: Función del baseline
      label: congelar la referencia operativa para evaluar cambios futuros, bandas colapsadas monitor_only y cobertura antes de reentrenar.
      wide: true
---
---
layout: tec-content
title: Drift AUTH real y decisión
projectName: Pricing MLOps AUTH Monitoring
ariaLabel: Drift AUTH real
media:
  kind: alert-strip
  ariaLabel: Señales de drift
  items:
    - value: "1,754"
      label: combos nuevos
    - value: 17.42%
      label: new combo rate
    - value: Red
      label: AUTH history drift
      variant: red
    - value: Yellow
      label: price drift
      variant: yellow
content:
  kind: two-column
  columns:
    - title: Lectura ejecutiva
      bullets:
        - La historia reciente cambió en composición o comportamiento.
        - "El impacto crítico por revenue se mantiene acotado: Red 1.16%, Yellow 7.26%."
        - Las alertas activan revisión, scoring/update y seguimiento; no un retraining automático.
    - type: decision
      label: Decisión recomendada
      body: Mantener modelo, ejecutar scoring/update para nuevos combos y continuar monitoreo.
---
---
layout: tec-content
title: "Parte 2: operación MLOps"
projectName: Pricing MLOps AUTH Monitoring
ariaLabel: Parte 2
media:
  kind: flow
  variant: ops
  ariaLabel: De notebook a operación
  items:
    - Notebook controlado
    - src/pricing
    - componentes Azure ML
    - Batch endpoint
content:
  kind: section-intro
  label: Objetivo de esta mitad
  text: Mostrar cómo la lógica analítica se volvió una ruta operativa versionable, invocable y auditable dentro de Azure ML.
  tags:
    - Repositorios claros
    - Componentes delgados
    - Componentes versionados
    - Storage MLOps
    - OIDC/RBAC
---
---
layout: tec-content
title: Qué recibimos desde análisis y notebooks
projectName: Pricing MLOps AUTH Monitoring
ariaLabel: Insumos de notebooks
media:
  kind: notebook-handoff
  ariaLabel: Handoff desde notebooks
  items:
    - value: Notebooks
      label: EDA, features, baseline y drift AUTH
    - value: Evidencia
      label: snapshots, métricas, thresholds y decision logs
    - value: Candidatos
      label: bloques analíticos listos para abstraer
content:
  kind: two-column
  columns:
    - title: Insumos analíticos
      bullets:
        - Los avances en notebooks documentaron long-tail, nulos estructurales, feature table y baseline.
        - Las reglas de validez y drift AUTH quedaron probadas con historia reciente.
        - "La decisión operacional ya tenía señales: combos nuevos, drift, readiness y acción recomendada."
    - title: Qué faltaba operar
      variant: muted
      text: El notebook sirve para análisis y explicación; para operación se necesitaba extraer funciones, contratos de entrada/salida, versionado y ejecución sin depender de una sesión manual.
---
---
layout: tec-content
title: Cómo se desglosó y abstrajo
projectName: Pricing MLOps AUTH Monitoring
ariaLabel: Abstracción de código reusable
media:
  kind: dual-run-flow
  ariaLabel: Progreso paralelo de notebook y Azure ML
  source:
    value: Código reusable
    label: src/pricing + src/pricing_mlops
  lanes:
    - label: Notebook
      items:
        - value: Import
          label: regla reusable
        - value: Validación
          label: análisis local
        - value: Evidencia
          label: métricas / drift
    - label: Operación
      items:
        - value: GitHub
          label: repo + workflow
        - value: CI/CD
          label: OIDC + registro
          variant: gate
        - value: Azure ML
          label: workspace
          variant: azure
        - value: Componente
          label: asset versionado
        - value: Pipeline
          label: batch endpoint
content:
  kind: two-column
  columns:
    - title: Ruta notebook
      bullets:
        - La lógica sale de celdas inline y queda reusable en `src/pricing`.
        - El notebook consume la función para análisis y debugging.
      examples:
        - label: Import
          code: from pricing.auth_monitoring.rules.auth_history_drift import calculate_auth_history_drift
        - label: Llamada
          code: result = calculate_auth_history_drift(..., run_id=run_id)
    - title: Ruta operación MLOps
      variant: muted
      bullets:
        - GitHub Actions autentica con OIDC/RBAC y registra assets.
        - `src/pricing_mlops` conecta Storage, componente y pipeline.
      examples:
        - label: CI/CD
          code: register_assets.py --config configs/azureml_auth_monitoring.yml
        - label: Componente
          code: run_monitoring_step.py --step calculate_auth_history_drift
        - label: Pipeline
          code: "component: azureml:pricing_mlops_calculate_auth_history_drift:0.1.3"
---
---
layout: tec-content
title: Repositorios y responsabilidades
projectName: Pricing MLOps AUTH Monitoring
ariaLabel: Repositorios y responsabilidades
media:
  kind: repo-split
  ariaLabel: Separación de repositorios
  items:
    - value: pricing-mlops-platform
      label: Base Azure, AML Workspace, Storage, Key Vault, App Insights, identidad y RBAC.
    - value: pricing-mlops
      label: Código ML, componentes Azure ML, pipeline, endpoint, manifest y outputs.
content:
  kind: two-column
  columns:
    - title: Plataforma Azure
      bullets:
        - "`pricing-mlops-platform` mantiene infraestructura y permisos compartidos."
        - Provisiona Storage, Azure ML Workspace, Key Vault, App Insights, identidades y RBAC.
        - Entrega la base para operar sin account keys ni connection strings.
    - title: Operación ML
      variant: muted
      bullets:
        - "`pricing-mlops` mantiene `src/pricing`, `src/pricing_mlops`, componentes, pipeline y endpoint."
        - Convierte lógica analítica en assets Azure ML registrados y versionados.
        - Publica evidencia funcional en Storage MLOps para auditoría.
---
---
layout: tec-content
title: Pipeline AzureML y outputs
projectName: Pricing MLOps AUTH Monitoring
ariaLabel: Pipeline AzureML
media:
  kind: pipeline-flow
  ariaLabel: Pipeline AzureML
  items:
    - validate_prepare
    - feature_engineering
    - prepare_history
    - monitoring_inputs
    - recommendation_validity
    - auth_history_drift
    - operational_decision
    - handoff
    - publish_outputs
    - notify
content:
  kind: two-column
  columns:
    - title: Activo operativo
      bullets:
        - "Endpoint: `pricing-auth-monitoring/blue`."
        - "Pipeline: `pricing_mlops_auth_monitoring_pipeline:0.1.18`."
        - "El componente `build_baseline_snapshot` existe como opt-in, no como camino default."
    - title: Outputs clave
      variant: muted
      text: "`model_run_log`, snapshots, drift logs, summaries, reports, manifest, handoff simulado y payload de notificación."
---
---
layout: tec-content
title: Decisión ejecutiva y roadmap
projectName: Pricing MLOps AUTH Monitoring
ariaLabel: Cierre ejecutivo
media:
  kind: roadmap
  ariaLabel: Roadmap MLOps
  items:
    - Foundation/MVP
    - Validation
    - Model health
    - Registry
    - Rollback
    - Auditoría
content:
  kind: two-column
  columns:
    - type: decision
      label: Decisión solicitada
      body: Continuar en validation con retraining gobernado por evidencia y sin vender el MVP como producción completa.
    - title: Antes de producción
      bullets:
        - Formalizar thresholds con negocio.
        - Agregar model health HB-SVI/S-curve.
        - Completar registry, champion/challenger, rollback, dashboard y auditoría productiva.
---
---
layout: tec-content
title: Azure Machine Learning Studio view
projectName: Pricing MLOps AUTH Monitoring
ariaLabel: Azure Machine Learning Studio view
media:
  kind: studio-view
  ariaLabel: Capturas de componentes y pipeline en Azure Machine Learning Studio
  items:
    - value: Components
      label: Componentes reutilizables y pipeline registrados con versiones en Azure ML.
      image: ./azureml-components-registry.png
      alt: Vista Components de Azure Machine Learning Studio
    - value: Pipeline run
      label: Ejecución completada con steps encadenados por flow token.
      image: ./azureml-pipeline-run.png
      alt: Vista de pipeline ejecutado en Azure Machine Learning Studio
---
