# Presentacion De Proyecto Equipo 46

Esta pagina documenta el rol general de cada slide del deck Slidev publicado en:

<a class="md-button md-button--primary" href="../slides/presentacion-proyecto-equipo-46/">Equipo 46 - Presentacion de Proyecto</a>

La presentacion esta pensada para una audiencia ejecutiva/academica. La narrativa se divide en dos bloques:

1. Trabajo analitico derivado de notebooks.
2. Operacion MLOps en Azure ML.

## Como Editar El Deck

El deck real esta en `presentations/slidev/presentacion-proyecto-equipo-46.md`.

Cada slide se edita desde frontmatter declarativo: `layout`, `title`, `projectName`, `media` y `content`. La estructura visual vive en layouts/componentes locales de Slidev, por lo que el Markdown no debe usar HTML embebido para maquetar.

Para cambiar contenido, edita los textos, bullets, metricas o listas dentro de `media` y `content`. Para cambiar distribucion visual, edita los layouts/componentes y estilos de `presentations/slidev`.

## Slide 1 - Portada

Presenta el proyecto, el equipo, la organizacion, asesor, patrocinador y fecha.

Introduce visualmente la idea de retraining por evidencia.

## Slide 2 - Tesis Ejecutiva

Explica el mensaje central: el modelo no debe reentrenarse por calendario, sino por evidencia operacional.

La decision MLOps se basa en cobertura, drift, validez y trazabilidad.

## Slide 3 - Parte 1: Notebooks A Evidencia MLOps

Abre el primer bloque de la presentacion.

Resume como el trabajo analitico en notebooks se convierte en evidencia medible: EDA, features, baseline y drift AUTH.

## Slide 4 - EDA + Feature Engineering

Resume la preparacion analitica: datos masked, nulos estructurales, long-tail, feature table y bandas P20-P85.

Conecta el analisis exploratorio con contratos reutilizables para monitoreo.

## Slide 5 - Baseline De Recomendaciones

Presenta el baseline operativo de recomendaciones.

Muestra metricas clave: 8,314 recomendaciones, 6,982 KPN, semaforo Green/Yellow/Red y funcion del baseline.

## Slide 6 - Drift AUTH Real Y Decision

Explica los resultados del monitoreo con historia AUTH reciente.

Muestra combos nuevos, drift AUTH, price drift y la decision recomendada: mantener modelo, hacer scoring/update y seguir monitoreando.

## Slide 7 - Metricas De Drift Para Decidir

Resume las señales usadas para convertir drift en una decisión ejecutiva.

Incluye cobertura, historia AUTH, precio, vigencia e impacto, con su métrica y uso ejecutivo.

## Slide 8 - Modelo Actual Y Monitoreo

Aclara la diferencia entre el modelo actual, el monitoreo ya implementado y el monitoreo avanzado pendiente.

El modelo actual sigue la ruta HB-SVI, elasticidad, S-curve, revenue/profit optimization y recomendacion. El monitoreo implementado cubre coverage, AUTH history drift, price drift, validity y scoring/update. El monitoreo avanzado pendiente queda como model health S-curve y elasticity health.

## Slide 9 - Parte 2: Operacion MLOps

Abre el segundo bloque de la presentacion.

Explica como se pasa de notebooks a operacion: repositorios claros, codigo reusable, registro Azure ML, componentes y batch endpoint.

## Slide 10 - Handoff Desde Notebooks

Resume el punto de partida de la segunda parte.

Los notebooks entregan EDA, feature engineering, baseline, drift AUTH, snapshots, metricas y decision logs. La slide explica que esos insumos funcionan para analisis, pero necesitan abstraerse para operar sin depender de una sesion manual.

## Slide 11 - Como Se Desgloso Y Abstrajo

Muestra como la logica estable pasa de celdas inline a modulos reutilizables.

Recupera el visual de doble ruta: notebook para analisis/validacion y Azure ML para operacion registrada. Incluye ejemplos cortos de import en notebook, wrapper de componente y referencia versionada dentro del pipeline.

## Slide 12 - Repositorios Y Responsabilidades

Describe la separacion de responsabilidades entre repositorios:

- `pricing-mlops-platform`: base Azure e infraestructura.
- `pricing-mlops`: operacion ML, componentes, pipeline, endpoint y artefactos.

La idea central es que la plataforma provee recursos y permisos, mientras el repo ML mantiene la logica y los assets operativos.

## Slide 13 - Pipeline AzureML Y Outputs

Muestra el flujo operativo del pipeline Azure ML.

Resume los pasos principales: validacion, feature engineering, historia AUTH, monitoreo, drift, decision, handoff, publicacion y notificacion.

## Slide 14 - Outputs Y Extensibilidad Operacional

Muestra un ejemplo concreto de output operacional de una corrida Azure ML y donde se guarda por el momento.

Usa como referencia el run `20260621T025500Z-new-auth-inputs`, su prefijo publicado en Storage MLOps y una vista compacta del `notification_payload.json`. La slide tambien muestra como leer el output: conteo de blobs por contenedor, filas de baseline/current AUTH, combos nuevos, semaforo y accion recomendada.

La ventaja modular queda conectada al ejemplo: el mismo payload puede alimentar notificaciones externas, auditoria en DB, dashboards BI o approval gates sin rehacer el pipeline completo.

## Slide 15 - Azure Machine Learning Studio View

Muestra evidencia visual desde Azure Machine Learning Studio.

Incluye la vista de componentes registrados y la vista de ejecucion del pipeline, para conectar la abstraccion de codigo con assets versionados y ejecuciones observables en Azure ML.
