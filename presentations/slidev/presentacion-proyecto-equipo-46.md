---
theme: default
title: "Plataforma MLOps para Pricing Intelligence en Azure"
canvasWidth: 960
colorSchema: light
transition: fade-out
drawings:
  persist: false
mdc: true
---

<div class="tec-cover-frame" aria-label="Portada de presentación">
  <aside class="tec-cover-rail" aria-label="Franja institucional">
    <img src="./public/tec-cover-rail.png" alt="" />
    <span>Presentación del Proyecto Integrador</span>
  </aside>

  <img class="tec-logo" src="./public/tec-posgrados.png" alt="Tecnológico de Monterrey Posgrados" />

  <div class="tec-program">
    Maestría en Inteligencia<br />
    Artificial Aplicada (MNA)
  </div>

  <figure class="tec-media-right tec-media-right--filled" aria-label="Retraining por evidencia">
    <div class="tec-cover-cycle">
      <span>Baseline</span>
      <span>Drift</span>
      <span>Decisión</span>
    </div>
    <strong>Retraining por evidencia</strong>
  </figure>

  <main class="tec-cover-title">
    <h1>Plataforma MLOps para Pricing Intelligence en Azure</h1>
    <p>AUTH Monitoring / Pricing</p>
  </main>

  <section class="tec-cover-meta" aria-label="Campos de portada">
    <div class="tec-meta-label">Presenta(n):</div>
    <ul class="tec-presenter-list">
      <li>Emanuel Flores Martinez</li>
      <li>Mario Javier Soriano Aguilera</li>
      <li>David Alberto Serrano Garcia</li>
    </ul>
    <div class="tec-meta-line">Asesor: <strong>Por confirmar</strong></div>
    <div class="tec-meta-line">Patrocinador(es): <strong>Mario</strong></div>
  </section>

  <div class="tec-date">Junio 2026</div>
</div>

---

<div class="tec-content-frame" aria-label="Tesis ejecutiva">
  <header class="tec-top-band" aria-label="Franja superior institucional">
    <img src="./public/tec-slide-top-band.png" alt="" />
    <div class="tec-section-mark">MNA</div>
    <div class="tec-project-name">Pricing MLOps AUTH Monitoring</div>
  </header>

  <h1>Tesis ejecutiva</h1>
  <figure class="tec-media-top tec-evidence-flow" aria-label="Flujo de decisión por evidencia">
    <span>Datos AUTH recientes</span>
    <i></i>
    <span>Drift operacional</span>
    <i></i>
    <span>Decisión MLOps</span>
  </figure>
  <main class="tec-content-area tec-two-col">
    <section class="tec-statement">
      <p>La decisión central es conservar, actualizar o reentrenar el modelo HB-SVI/S-curve sólo cuando la evidencia operacional lo justifique.</p>
    </section>
    <section class="tec-decision-stack">
      <div><strong>No</strong><span>retraining mensual por rutina</span></div>
      <div><strong>Sí</strong><span>coverage, drift, validez y decisión trazable</span></div>
      <div><strong>Hoy</strong><span>foundation/MVP en ruta a validation</span></div>
    </section>
  </main>
</div>

---

<div class="tec-content-frame" aria-label="Parte 1">
  <header class="tec-top-band" aria-label="Franja superior institucional">
    <img src="./public/tec-slide-top-band.png" alt="" />
    <div class="tec-section-mark">MNA</div>
    <div class="tec-project-name">Pricing MLOps AUTH Monitoring</div>
  </header>

  <h1>Parte 1: notebooks a evidencia MLOps</h1>
  <figure class="tec-media-top tec-timeline" aria-label="Avances analíticos">
    <div><strong>Avance 1</strong><span>EDA</span></div>
    <div><strong>Avance 2</strong><span>Features</span></div>
    <div><strong>Avance 3</strong><span>Baseline</span></div>
    <div><strong>Avance 4</strong><span>Drift AUTH</span></div>
  </figure>
  <main class="tec-content-area tec-section-intro">
    <strong>Objetivo de esta mitad</strong>
    <p>Convertir exploración de notebooks en evidencia medible: calidad, features, baseline, drift y decisión operacional.</p>
    <div class="tec-tag-row">
      <span>Datos masked</span>
      <span>Contratos de columnas</span>
      <span>Artefactos versionables</span>
      <span>AUTH-only scope</span>
    </div>
  </main>
</div>

---

<div class="tec-content-frame" aria-label="EDA y feature engineering">
  <header class="tec-top-band" aria-label="Franja superior institucional">
    <img src="./public/tec-slide-top-band.png" alt="" />
    <div class="tec-section-mark">MNA</div>
    <div class="tec-project-name">Pricing MLOps AUTH Monitoring</div>
  </header>

  <h1>EDA + feature engineering</h1>
  <figure class="tec-media-top tec-kpi-strip" aria-label="Hallazgos de preparación">
    <div><strong>~234k</strong><span>filas masked de entrada</span></div>
    <div><strong>Nulos</strong><span>estructurales</span></div>
    <div><strong>8,314</strong><span>filas de feature table</span></div>
    <div><strong>P20-P85</strong><span>bandas de monitoreo</span></div>
  </figure>
  <main class="tec-content-area tec-two-col">
    <section class="tec-bullet-panel">
      <h2>Lo que se resolvió</h2>
      <ul>
        <li>Perfilar long-tail de precio/cantidad sin tratarlo como error automático.</li>
        <li>Separar nulos estructurales de fallas reales de origen.</li>
        <li>Construir features de demanda, precio, margen, bins, cobertura y llaves técnicas.</li>
      </ul>
    </section>
    <section class="tec-bullet-panel tec-panel-muted">
      <h2>Implicación MLOps</h2>
      <p>La feature table se vuelve contrato entre notebooks, componentes Azure ML, baseline y monitoreo AUTH.</p>
    </section>
  </main>
</div>

---

<div class="tec-content-frame" aria-label="Baseline MLOps">
  <header class="tec-top-band" aria-label="Franja superior institucional">
    <img src="./public/tec-slide-top-band.png" alt="" />
    <div class="tec-section-mark">MNA</div>
    <div class="tec-project-name">Pricing MLOps AUTH Monitoring</div>
  </header>

  <h1>Baseline de recomendaciones</h1>
  <figure class="tec-media-top tec-status-band" aria-label="Semáforo baseline">
    <div class="tec-status tec-status-green" style="--w: 61.58%"><span>Green 61.58%</span></div>
    <div class="tec-status tec-status-yellow" style="--w: 38.42%"><span>Yellow 38.42%</span></div>
    <div class="tec-status tec-status-red" style="--w: 0%"><span>Red 0%</span></div>
  </figure>
  <main class="tec-content-area tec-kpi-grid">
    <div class="tec-kpi-card"><strong>8,314</strong><span>recomendaciones congeladas</span></div>
    <div class="tec-kpi-card"><strong>6,982</strong><span>KPN representados</span></div>
    <div class="tec-kpi-card"><strong>0%</strong><span>casos Red en baseline</span></div>
    <div class="tec-kpi-card tec-kpi-wide"><strong>Función del baseline</strong><span>congelar la referencia operativa para evaluar cambios futuros, bandas colapsadas monitor_only y cobertura antes de reentrenar.</span></div>
  </main>
</div>

---

<div class="tec-content-frame" aria-label="Drift AUTH real">
  <header class="tec-top-band" aria-label="Franja superior institucional">
    <img src="./public/tec-slide-top-band.png" alt="" />
    <div class="tec-section-mark">MNA</div>
    <div class="tec-project-name">Pricing MLOps AUTH Monitoring</div>
  </header>

  <h1>Drift AUTH real y decisión</h1>
  <figure class="tec-media-top tec-alert-strip" aria-label="Señales de drift">
    <div><strong>1,754</strong><span>combos nuevos</span></div>
    <div><strong>17.42%</strong><span>new combo rate</span></div>
    <div class="is-red"><strong>Red</strong><span>AUTH history drift</span></div>
    <div class="is-yellow"><strong>Yellow</strong><span>price drift</span></div>
  </figure>
  <main class="tec-content-area tec-two-col">
    <section class="tec-bullet-panel">
      <h2>Lectura ejecutiva</h2>
      <ul>
        <li>La historia reciente cambió en composición o comportamiento.</li>
        <li>El impacto crítico por revenue se mantiene acotado: Red 1.16%, Yellow 7.26%.</li>
        <li>Las alertas activan revisión, scoring/update y seguimiento; no un retraining automático.</li>
      </ul>
    </section>
    <section class="tec-decision-card">
      <span>Decisión recomendada</span>
      <strong>Mantener modelo, ejecutar scoring/update para nuevos combos y continuar monitoreo.</strong>
    </section>
  </main>
</div>

---

<div class="tec-content-frame" aria-label="Parte 2">
  <header class="tec-top-band" aria-label="Franja superior institucional">
    <img src="./public/tec-slide-top-band.png" alt="" />
    <div class="tec-section-mark">MNA</div>
    <div class="tec-project-name">Pricing MLOps AUTH Monitoring</div>
  </header>

  <h1>Parte 2: operación MLOps</h1>
  <figure class="tec-media-top tec-ops-flow" aria-label="De notebook a operación">
    <span>Notebook controlado</span>
    <i></i>
    <span>src/pricing</span>
    <i></i>
    <span>wrappers Azure ML</span>
    <i></i>
    <span>Batch endpoint</span>
  </figure>
  <main class="tec-content-area tec-section-intro">
    <strong>Objetivo de esta mitad</strong>
    <p>Mostrar cómo la lógica analítica se volvió una ruta operativa versionable, invocable y auditable dentro de Azure ML.</p>
    <div class="tec-tag-row">
      <span>Componentes delgados</span>
      <span>Pipeline versionado</span>
      <span>Storage MLOps</span>
      <span>OIDC/RBAC</span>
    </div>
  </main>
</div>

---

<div class="tec-content-frame" aria-label="Arquitectura vigente">
  <header class="tec-top-band" aria-label="Franja superior institucional">
    <img src="./public/tec-slide-top-band.png" alt="" />
    <div class="tec-section-mark">MNA</div>
    <div class="tec-project-name">Pricing MLOps AUTH Monitoring</div>
  </header>

  <h1>Arquitectura vigente</h1>
  <figure class="tec-media-top tec-repo-split" aria-label="Separación de repositorios">
    <div><strong>pricing-mlops-platform</strong><span>IaC/base Azure: Storage, AML Workspace, Key Vault, App Insights, identidad, RBAC y cpu-cluster.</span></div>
    <div><strong>pricing-mlops</strong><span>Operación ML: componentes, pipeline, endpoint, smoke test y publicación de artefactos.</span></div>
  </figure>
  <main class="tec-content-area tec-two-col">
    <section class="tec-bullet-panel">
      <h2>Runtime vigente</h2>
      <ul>
        <li>Azure ML batch endpoint como entrada administrada.</li>
        <li>Pipeline component/job como capa de ejecución.</li>
        <li>Storage MLOps particionado por environment, trigger, owner, fecha y run_id.</li>
      </ul>
    </section>
    <section class="tec-bullet-panel tec-panel-muted">
      <h2>Límite explícito</h2>
      <p>Staging y validation están habilitados. No hay prod, Private Endpoints, ADF, Functions operativas, SQL audit activo ni endpoint online.</p>
    </section>
  </main>
</div>

---

<div class="tec-content-frame" aria-label="Pipeline AzureML">
  <header class="tec-top-band" aria-label="Franja superior institucional">
    <img src="./public/tec-slide-top-band.png" alt="" />
    <div class="tec-section-mark">MNA</div>
    <div class="tec-project-name">Pricing MLOps AUTH Monitoring</div>
  </header>

  <h1>Pipeline AzureML y outputs</h1>
  <figure class="tec-media-top tec-pipeline-flow" aria-label="Pipeline AzureML">
    <span>validate_prepare</span>
    <span>feature_engineering</span>
    <span>prepare_history</span>
    <span>monitoring_inputs</span>
    <span>recommendation_validity</span>
    <span>auth_history_drift</span>
    <span>operational_decision</span>
    <span>handoff</span>
    <span>publish_outputs</span>
    <span>notify</span>
  </figure>
  <main class="tec-content-area tec-two-col">
    <section class="tec-bullet-panel">
      <h2>Activo operativo</h2>
      <ul>
        <li>Endpoint: <code>pricing-auth-monitoring/blue</code>.</li>
        <li>Pipeline: <code>pricing_mlops_auth_monitoring_pipeline:0.1.18</code>.</li>
        <li>El componente <code>build_baseline_snapshot</code> existe como opt-in, no como camino default.</li>
      </ul>
    </section>
    <section class="tec-bullet-panel tec-panel-muted">
      <h2>Outputs clave</h2>
      <p><code>model_run_log</code>, snapshots, drift logs, summaries, reports, manifest, handoff simulado y payload de notificación.</p>
    </section>
  </main>
</div>

---

<div class="tec-content-frame" aria-label="Cierre ejecutivo">
  <header class="tec-top-band" aria-label="Franja superior institucional">
    <img src="./public/tec-slide-top-band.png" alt="" />
    <div class="tec-section-mark">MNA</div>
    <div class="tec-project-name">Pricing MLOps AUTH Monitoring</div>
  </header>

  <h1>Decisión ejecutiva y roadmap</h1>
  <figure class="tec-media-top tec-roadmap" aria-label="Roadmap MLOps">
    <span>Foundation/MVP</span>
    <span>Validation</span>
    <span>Model health</span>
    <span>Registry</span>
    <span>Rollback</span>
    <span>Auditoría</span>
  </figure>
  <main class="tec-content-area tec-two-col">
    <section class="tec-decision-card">
      <span>Decisión solicitada</span>
      <strong>Continuar en validation con retraining gobernado por evidencia y sin vender el MVP como producción completa.</strong>
    </section>
    <section class="tec-bullet-panel">
      <h2>Antes de producción</h2>
      <ul>
        <li>Formalizar thresholds con negocio.</li>
        <li>Agregar model health HB-SVI/S-curve.</li>
        <li>Completar registry, champion/challenger, rollback, dashboard y auditoría productiva.</li>
      </ul>
    </section>
  </main>
</div>
