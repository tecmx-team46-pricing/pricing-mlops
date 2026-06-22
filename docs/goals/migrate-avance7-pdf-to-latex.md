# Goal: Migrar Avance 7 PDF A LaTeX

## Objetivo

Migrar el PDF `Avance7_Equipo46_Resumen_Ejecutivo_MLOps_Pricing_Azure_v3.pdf` a un documento LaTeX versionable dentro de `pricing-mlops`, conservando el contenido histórico del PDF y dejando un flujo de verificación reproducible.

## Fuente

```text
/Users/me/Downloads/Avance7_Equipo46_Resumen_Ejecutivo_MLOps_Pricing_Azure_v3.pdf
```

Propiedades observadas:

- Formato: PDF letter.
- Páginas: 8.
- Tema: resumen ejecutivo de Plataforma MLOps para Pricing Intelligence en Azure.
- Enfoque: reentrenar por evidencia, no por calendario.

## Archivos Esperados

```text
docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure.tex
docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure.pdf
docs/goals/migrate-avance7-pdf-to-latex.md
```

El PDF compilado se versiona en `docs/project/` por solicitud explícita de cierre de este goal. Para iteraciones futuras, generar primero fuera del repo y copiar sólo el PDF final aprobado.

## Decisiones De Migración

- La migración conserva el documento como fuente histórica.
- El cuerpo del `.tex` no corrige la narrativa del PDF, aunque mencione Azure Function y Azure SQL audit.
- Las figuras se recrean como TikZ editable.
- El documento LaTeX es autocontenido y no requiere imágenes externas.
- El PDF final queda versionado junto al `.tex`.
- Cualquier diferencia contra la infraestructura actual debe documentarse fuera del cuerpo principal si se necesita una versión corregida posterior.

## Checklist De Implementación

- [x] Crear `docs/project/`.
- [x] Crear `docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure.tex`.
- [x] Incluir portada/resumen de decisión.
- [x] Migrar secciones 1 a 11.
- [x] Migrar cierre para comité ejecutivo y anexo.
- [x] Recrear tablas del PDF con `booktabs`, `tabularx` o `longtable`.
- [x] Recrear figuras 1 a 4 con TikZ editable.
- [x] Mantener frases y métricas clave:
  - reentrenar por evidencia, no por calendario;
  - HB-SVI;
  - S-curve;
  - drift;
  - scoring/update;
  - staging/validation;
  - 8,314 recomendaciones;
  - 6,982 KPN;
  - 1,754 combos nuevos;
  - 17.42%;
  - Red 1.16%;
  - Yellow 7.26%.
- [x] Compilar con `latexmk` usando `xelatex`.
- [x] Revisar visualmente el PDF generado.
- [x] Confirmar que no haya marcadores de contenido pendiente.
- [x] Copiar el PDF final versionado a `docs/project/`.

## Comandos De Compilación

Ejecutar desde la raíz de `pricing-mlops`:

```bash
rm -rf /tmp/pricing-mlops-avance7-latex
mkdir -p /tmp/pricing-mlops-avance7-latex
latexmk -xelatex -interaction=nonstopmode -halt-on-error \
  -output-directory=/tmp/pricing-mlops-avance7-latex \
  docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure.tex
```

Salida esperada:

```text
/tmp/pricing-mlops-avance7-latex/avance7-resumen-ejecutivo-mlops-pricing-azure.pdf
```

Publicación del PDF final versionado:

```bash
cp /tmp/pricing-mlops-avance7-latex/avance7-resumen-ejecutivo-mlops-pricing-azure.pdf \
  docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure.pdf
```

## Verificación

Comandos recomendados:

```bash
pdfinfo /tmp/pricing-mlops-avance7-latex/avance7-resumen-ejecutivo-mlops-pricing-azure.pdf
rg -n "T[B]D|T[O]DO|place[ -]?holder|contenido[[:space:]]+faltante" docs/project/avance7-resumen-ejecutivo-mlops-pricing-azure.tex docs/goals/migrate-avance7-pdf-to-latex.md
git status --short docs/project docs/goals
```

Criterios de aceptación:

- La compilación termina sin errores.
- El PDF generado abre correctamente.
- La paginación es razonable para el contenido migrado.
- Las tablas no quedan cortadas de forma ilegible.
- Las figuras aparecen como diagramas editables, no como imágenes externas.
- El `.tex` conserva el contenido histórico del PDF.
- El goal deja claro cómo retomar, compilar y verificar el entregable.

## Nota Operativa

Este goal conserva la narrativa del PDF como documento histórico. En la implementación actual del proyecto, la arquitectura activa puede diferir de algunas frases del documento, por ejemplo las menciones a Azure Function o Azure SQL audit. Esas correcciones no forman parte de esta migración fiel; deben abordarse en una versión editorial separada si negocio o el comité piden una versión actualizada.
