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
    - wrappers Azure ML
    - Batch endpoint
content:
  kind: section-intro
  label: Objetivo de esta mitad
  text: Mostrar cómo la lógica analítica se volvió una ruta operativa versionable, invocable y auditable dentro de Azure ML.
  tags:
    - Componentes delgados
    - Pipeline versionado
    - Storage MLOps
    - OIDC/RBAC
---
---
layout: tec-content
title: Arquitectura vigente
projectName: Pricing MLOps AUTH Monitoring
ariaLabel: Arquitectura vigente
media:
  kind: dual-run-flow
  ariaLabel: Código reusable ejecutable en notebooks y componentes Azure ML
  source:
    value: Código reusable
    label: src/pricing
  lanes:
    - label: Análisis
      items:
        - value: Notebook
          label: exploración
        - value: Análisis
          label: bloques código
        - value: Evidencia
          label: EDA / drift
    - label: Operación
      items:
        - value: Actions
          label: OIDC CI/CD
        - value: Componente AML
          label: registro
        - value: Endpoint
          label: batch blue
content:
  kind: two-column
  columns:
    - title: Repositorios y responsabilidad
      bullets:
        - "`pricing-mlops-platform` mantiene la base Azure: Storage, AML Workspace, Key Vault, App Insights, identidad, RBAC y cluster."
        - "`pricing-mlops` mantiene lógica reusable en `src/pricing`, consumible desde notebooks y wrappers Azure ML."
        - GitHub Actions autentica con OIDC/RBAC y registra componentes para ejecución gobernada.
    - title: Registro Azure ML
      variant: muted
      bullets:
        - Los mismos bloques analíticos se validan en notebook y se empaquetan como componentes versionados.
        - El pipeline usa esas versiones para publicar el batch endpoint `pricing-auth-monitoring/blue`.
        - Los outputs quedan trazables en Storage MLOps y logs de ejecución.
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
