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

## Slide 7 - Parte 2: Operacion MLOps

Abre el segundo bloque de la presentacion.

Explica como se pasa de notebooks a operacion: repositorios claros, codigo reusable, registro Azure ML, componentes y batch endpoint.

## Slide 8 - Que Recibimos Desde Analisis Y Notebooks

Resume el punto de partida de la segunda parte.

Los notebooks entregan EDA, feature engineering, baseline, drift AUTH, snapshots, metricas y decision logs. La slide explica que esos insumos funcionan para analisis, pero necesitan abstraerse para operar sin depender de una sesion manual.

## Slide 9 - Como Se Desgloso Y Abstrajo

Muestra como la logica estable pasa de celdas inline a modulos reutilizables.

Recupera el visual de doble ruta: notebook para analisis/validacion y Azure ML para operacion registrada. Incluye ejemplos cortos de import en notebook, wrapper de componente y referencia versionada dentro del pipeline.

## Slide 10 - Repositorios Y Responsabilidades

Describe la separacion de responsabilidades entre repositorios:

- `pricing-mlops-platform`: base Azure e infraestructura.
- `pricing-mlops`: operacion ML, componentes, pipeline, endpoint y artefactos.

La idea central es que la plataforma provee recursos y permisos, mientras el repo ML mantiene la logica y los assets operativos.

## Slide 11 - Registro ML Y CI/CD

Explica el flujo de publicacion operacional:

GitHub, GitHub Actions, autenticacion OIDC/RBAC, registro de assets Azure ML, manifest de release y batch endpoint.

## Slide 12 - Pipeline AzureML Y Outputs

Muestra el flujo operativo del pipeline Azure ML.

Resume los pasos principales: validacion, feature engineering, historia AUTH, monitoreo, drift, decision, handoff, publicacion y notificacion.

## Slide 13 - Decision Ejecutiva Y Roadmap

Cierra con la recomendacion ejecutiva.

Propone continuar hacia validation con retraining gobernado por evidencia y lista pendientes antes de produccion: thresholds, model health, registry, rollback, dashboard y auditoria productiva.
