# Presentacion De Proyecto Equipo 46

Esta pagina documenta el rol general de cada slide del deck Slidev publicado en:

<a class="md-button md-button--primary" href="../slides/presentacion-proyecto-equipo-46/">Equipo 46 - Presentacion de Proyecto</a>

La presentacion esta pensada para una audiencia ejecutiva/academica. La narrativa se divide en dos bloques:

1. Trabajo analitico derivado de notebooks.
2. Operacion MLOps en Azure ML.

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

## Slide 7 - Parte 2: Operacion MLOps

Abre el segundo bloque de la presentacion.

Explica como se pasa de notebooks a operacion: codigo reusable, wrappers Azure ML, componentes y batch endpoint.

## Slide 8 - Arquitectura Vigente

Describe la arquitectura actual separando responsabilidades:

- `pricing-mlops-platform`: base Azure e infraestructura.
- `pricing-mlops`: operacion ML, componentes, pipeline, endpoint y artefactos.

Tambien aclara limites actuales: no prod, no SQL audit activo, no Azure Functions operativas.

## Slide 9 - Pipeline AzureML Y Outputs

Muestra el flujo operativo del pipeline Azure ML.

Resume los pasos principales: validacion, feature engineering, historia AUTH, monitoreo, drift, decision, handoff, publicacion y notificacion.

## Slide 10 - Decision Ejecutiva Y Roadmap

Cierra con la recomendacion ejecutiva.

Propone continuar hacia validation con retraining gobernado por evidencia y lista pendientes antes de produccion: thresholds, model health, registry, rollback, dashboard y auditoria productiva.
