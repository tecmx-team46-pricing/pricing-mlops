# Pricing MLOps

`pricing-mlops` es el repo funcional del flujo AUTH monitoring. Aqui vive la logica que viene de notebooks, los componentes Azure ML, el pipeline component, el batch endpoint y los scripts para registrar, desplegar e invocar corridas.

`pricing-mlops-platform` crea la base Azure: resource groups, Storage, Azure ML Workspace, identidades y RBAC. Este repo consume esos recursos mediante variables como `AZURE_RESOURCE_GROUP`, `AZURE_ML_WORKSPACE`, `AZURE_STORAGE_ACCOUNT` y `AZURE_ML_JOB_IDENTITY_CLIENT_ID`.

## Ruta Operativa

```text
Notebook controlado
-> codigo reusable en src/pricing/*
-> wrapper delgado en scripts/components/*
-> component YAML en azureml/components/*
-> pipeline YAML en azureml/pipelines/*
-> batch endpoint en azureml/endpoints/*
-> Storage MLOps outputs
```

## Para Quien Es Esta Documentacion

- Personas que estan pasando logica de notebooks a componentes Azure ML.
- MLOps que registra componentes, pipeline component y endpoint.
- Analistas que necesitan correr el pipeline y encontrar resultados.
- Revisores que necesitan entender que se publica en Storage y que no debe entrar a git.

## Comandos Base

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m compileall src scripts tests
python -m pytest
```

## GitHub Pages

Este sitio se construye con MkDocs. Para verlo localmente:

```bash
python -m pip install -r requirements-docs.txt
mkdocs serve
mkdocs build --strict
```

GitHub Pages debe estar configurado en el repo con source `GitHub Actions`. El workflow `docs` construye en pull request y despliega en `push` a `main` o `workflow_dispatch`.

## Presentacion Slidev

La plantilla base de la presentacion del proyecto se publica como parte del mismo sitio:

<a class="md-button md-button--primary" href="slides/presentacion-proyecto-equipo-46/">Equipo 46 - Presentacion de Proyecto</a>
