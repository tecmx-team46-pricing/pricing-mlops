# Python Azure ML Registration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Azure ML asset registration/deployment orchestration from shell-heavy scripts to Python SDK-driven scripts while keeping the existing YAML contracts and GitHub Actions behavior.

**Architecture:** YAML files remain the source of truth for Azure ML environments, components, pipeline component, batch endpoint, and deployment. Python scripts load a small release config, validate local file contracts, call `azure-ai-ml` SDK APIs, and preserve the existing shell wrappers as compatibility entrypoints until the workflow is switched.

**Tech Stack:** Python 3.11+, `azure-ai-ml`, `azure-identity`, PyYAML, pytest, existing Azure ML YAML specs.

---

## File Structure

- Create: `configs/azureml_auth_monitoring.yml`
  - Central release config listing environment, components, pipeline, endpoint, deployment, manifest, default resource group/workspace, and expected subscription name.
- Create: `scripts/azureml/__init__.py`
  - Package marker for Azure ML deployment helpers.
- Create: `scripts/azureml/config.py`
  - Loads and validates the central config with typed dataclasses.
- Create: `scripts/azureml/client.py`
  - Builds `MLClient` from environment variables and config defaults.
- Create: `scripts/azureml/register_assets.py`
  - Registers environment, command components, and pipeline component from YAML with the Azure ML Python SDK.
- Create: `scripts/azureml/deploy_endpoint.py`
  - Deploys/updates batch endpoint and deployment from YAML with the Azure ML Python SDK.
- Create: `tests/test_azureml_python_registration.py`
  - Tests config parsing, file validation, component list coverage, manifest consistency, and workflow migration expectations.
- Modify: `.github/workflows/azureml-components.yml`
  - Switch registration and deployment steps from shell scripts to Python scripts after tests exist.
- Modify: `scripts/register_azureml_components.sh`
  - Keep as compatibility wrapper that calls `python scripts/azureml/register_assets.py`.
- Modify: `scripts/deploy_auth_monitoring_batch_endpoint.sh`
  - Keep as compatibility wrapper that calls `python scripts/azureml/deploy_endpoint.py`.
- Modify: `README.md`
  - Document Python commands as primary path and shell wrappers as compatibility.
- Modify: `docs/runbook.md`
  - Document local smoke remains local and Python handles deploy orchestration.

---

### Task 1: Add Central Azure ML Release Config

**Files:**
- Create: `configs/azureml_auth_monitoring.yml`
- Test: `tests/test_azureml_python_registration.py`

- [ ] **Step 1: Write the failing config coverage tests**

Create `tests/test_azureml_python_registration.py` with:

```python
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / "configs" / "azureml_auth_monitoring.yml"
MANIFEST_FILE = ROOT / "azureml" / "manifests" / "auth-monitoring-release.json"
WORKFLOW_FILE = ROOT / ".github" / "workflows" / "azureml-components.yml"


def test_azureml_release_config_lists_existing_assets():
    config = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))

    asset_paths = [
        config["environment"],
        *config["components"],
        config["pipeline"],
        config["endpoint"]["endpoint_file"],
        config["endpoint"]["deployment_file"],
        config["manifest"],
    ]

    for relative_path in asset_paths:
        assert (ROOT / relative_path).is_file(), relative_path


def test_azureml_release_config_matches_auth_monitoring_contract():
    config = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))

    assert config["subscription_name"] == "Tecmx"
    assert config["resource_group"] == "rg-pricing-mlops-main"
    assert config["workspace"] == "mlw-pmlops-06152240"
    assert config["endpoint"]["name"] == "pricing-auth-monitoring"
    assert config["endpoint"]["deployment"] == "blue"
    assert config["pipeline"] == "azureml/pipelines/auth_monitoring_pipeline.yml"
    assert config["manifest"] == "azureml/manifests/auth-monitoring-release.json"
    assert "azureml/components/validate_prepare.yml" in config["components"]
    assert "azureml/components/publish_outputs.yml" in config["components"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_azureml_python_registration.py -q
```

Expected: FAIL because `configs/azureml_auth_monitoring.yml` does not exist.

- [ ] **Step 3: Add the central config**

Create `configs/azureml_auth_monitoring.yml`:

```yaml
subscription_name: Tecmx
resource_group: rg-pricing-mlops-main
workspace: mlw-pmlops-06152240

environment: azureml/environment.yml

components:
  - azureml/components/validate_prepare.yml
  - azureml/components/build_monitoring_inputs.yml
  - azureml/components/calculate_recommendation_validity.yml
  - azureml/components/calculate_auth_history_drift.yml
  - azureml/components/calculate_operational_decision.yml
  - azureml/components/publish_outputs.yml

pipeline: azureml/pipelines/auth_monitoring_pipeline.yml

endpoint:
  name: pricing-auth-monitoring
  deployment: blue
  endpoint_file: azureml/endpoints/auth-monitoring-batch-endpoint.yml
  deployment_file: azureml/endpoints/auth-monitoring-batch-deployment.yml

manifest: azureml/manifests/auth-monitoring-release.json
```

- [ ] **Step 4: Run tests to verify config coverage passes**

Run:

```bash
python -m pytest tests/test_azureml_python_registration.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add configs/azureml_auth_monitoring.yml tests/test_azureml_python_registration.py
git commit -m "Add Azure ML release config"
```

---

### Task 2: Add Typed Config Loader

**Files:**
- Create: `scripts/azureml/__init__.py`
- Create: `scripts/azureml/config.py`
- Modify: `tests/test_azureml_python_registration.py`

- [ ] **Step 1: Extend tests for typed config loading**

Append to `tests/test_azureml_python_registration.py`:

```python
from scripts.azureml.config import load_release_config


def test_load_release_config_resolves_paths():
    config = load_release_config(CONFIG_FILE, repo_root=ROOT)

    assert config.subscription_name == "Tecmx"
    assert config.resource_group == "rg-pricing-mlops-main"
    assert config.workspace == "mlw-pmlops-06152240"
    assert config.environment.path == ROOT / "azureml/environment.yml"
    assert len(config.components) == 6
    assert config.pipeline.path == ROOT / "azureml/pipelines/auth_monitoring_pipeline.yml"
    assert config.endpoint.name == "pricing-auth-monitoring"
    assert config.endpoint.deployment == "blue"
    assert config.manifest.path == ROOT / "azureml/manifests/auth-monitoring-release.json"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_azureml_python_registration.py::test_load_release_config_resolves_paths -q
```

Expected: FAIL because `scripts.azureml.config` does not exist.

- [ ] **Step 3: Create package marker**

Create `scripts/azureml/__init__.py`:

```python
"""Azure ML deployment helpers for pricing-mlops."""
```

- [ ] **Step 4: Implement config loader**

Create `scripts/azureml/config.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AssetFile:
    path: Path


@dataclass(frozen=True)
class EndpointConfig:
    name: str
    deployment: str
    endpoint_file: AssetFile
    deployment_file: AssetFile


@dataclass(frozen=True)
class ReleaseConfig:
    subscription_name: str
    resource_group: str
    workspace: str
    environment: AssetFile
    components: tuple[AssetFile, ...]
    pipeline: AssetFile
    endpoint: EndpointConfig
    manifest: AssetFile


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _asset_file(repo_root: Path, relative_path: str) -> AssetFile:
    path = repo_root / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"Azure ML asset file not found: {path}")
    return AssetFile(path=path)


def load_release_config(path: Path, *, repo_root: Path) -> ReleaseConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Azure ML release config must be a mapping")

    endpoint_data = data.get("endpoint")
    if not isinstance(endpoint_data, dict):
        raise ValueError("endpoint must be a mapping")

    component_paths = data.get("components")
    if not isinstance(component_paths, list) or not component_paths:
        raise ValueError("components must be a non-empty list")
    if not all(isinstance(component_path, str) for component_path in component_paths):
        raise ValueError("components entries must be strings")

    return ReleaseConfig(
        subscription_name=_required_string(data, "subscription_name"),
        resource_group=_required_string(data, "resource_group"),
        workspace=_required_string(data, "workspace"),
        environment=_asset_file(repo_root, _required_string(data, "environment")),
        components=tuple(_asset_file(repo_root, component_path) for component_path in component_paths),
        pipeline=_asset_file(repo_root, _required_string(data, "pipeline")),
        endpoint=EndpointConfig(
            name=_required_string(endpoint_data, "name"),
            deployment=_required_string(endpoint_data, "deployment"),
            endpoint_file=_asset_file(repo_root, _required_string(endpoint_data, "endpoint_file")),
            deployment_file=_asset_file(repo_root, _required_string(endpoint_data, "deployment_file")),
        ),
        manifest=_asset_file(repo_root, _required_string(data, "manifest")),
    )
```

- [ ] **Step 5: Run tests**

Run:

```bash
python -m pytest tests/test_azureml_python_registration.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/azureml/__init__.py scripts/azureml/config.py tests/test_azureml_python_registration.py
git commit -m "Load Azure ML release config in Python"
```

---

### Task 3: Add MLClient Factory

**Files:**
- Create: `scripts/azureml/client.py`
- Modify: `tests/test_azureml_python_registration.py`

- [ ] **Step 1: Add tests for environment override behavior**

Append to `tests/test_azureml_python_registration.py`:

```python
from scripts.azureml.client import AzureMlSettings


def test_azureml_settings_uses_env_overrides(monkeypatch):
    config = load_release_config(CONFIG_FILE, repo_root=ROOT)
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "sub-from-env")
    monkeypatch.setenv("AZURE_RESOURCE_GROUP", "rg-from-env")
    monkeypatch.setenv("AZURE_ML_WORKSPACE", "workspace-from-env")

    settings = AzureMlSettings.from_config(config)

    assert settings.subscription_id == "sub-from-env"
    assert settings.resource_group == "rg-from-env"
    assert settings.workspace == "workspace-from-env"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_azureml_python_registration.py::test_azureml_settings_uses_env_overrides -q
```

Expected: FAIL because `scripts.azureml.client` does not exist.

- [ ] **Step 3: Implement client helper**

Create `scripts/azureml/client.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass

from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

from scripts.azureml.config import ReleaseConfig


@dataclass(frozen=True)
class AzureMlSettings:
    subscription_id: str
    resource_group: str
    workspace: str

    @classmethod
    def from_config(cls, config: ReleaseConfig) -> "AzureMlSettings":
        subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID", "")
        if not subscription_id:
            raise ValueError("AZURE_SUBSCRIPTION_ID is required")
        return cls(
            subscription_id=subscription_id,
            resource_group=os.environ.get("AZURE_RESOURCE_GROUP", config.resource_group),
            workspace=os.environ.get("AZURE_ML_WORKSPACE", config.workspace),
        )


def build_ml_client(settings: AzureMlSettings) -> MLClient:
    return MLClient(
        DefaultAzureCredential(),
        settings.subscription_id,
        settings.resource_group,
        settings.workspace,
    )
```

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_azureml_python_registration.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/azureml/client.py tests/test_azureml_python_registration.py
git commit -m "Add Azure ML Python client factory"
```

---

### Task 4: Implement Python Asset Registration

**Files:**
- Create: `scripts/azureml/register_assets.py`
- Modify: `tests/test_azureml_python_registration.py`
- Modify: `scripts/register_azureml_components.sh`

- [ ] **Step 1: Add tests for registration script source**

Append to `tests/test_azureml_python_registration.py`:

```python
REGISTER_ASSETS = ROOT / "scripts" / "azureml" / "register_assets.py"
REGISTER_WRAPPER = ROOT / "scripts" / "register_azureml_components.sh"


def test_register_assets_uses_python_sdk_loaders():
    source = REGISTER_ASSETS.read_text(encoding="utf-8")

    assert "load_component" in source
    assert "load_environment" in source
    assert "ml_client.components.create_or_update" in source
    assert "ml_client.environments.create_or_update" in source
    assert "az ml component create" not in source


def test_register_shell_wrapper_delegates_to_python():
    source = REGISTER_WRAPPER.read_text(encoding="utf-8")

    assert "python" in source
    assert "scripts/azureml/register_assets.py" in source
    assert "az ml component create" not in source
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_azureml_python_registration.py::test_register_assets_uses_python_sdk_loaders tests/test_azureml_python_registration.py::test_register_shell_wrapper_delegates_to_python -q
```

Expected: FAIL because script is missing and wrapper still uses CLI.

- [ ] **Step 3: Implement Python registration script**

Create `scripts/azureml/register_assets.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path

from azure.ai.ml import load_component, load_environment

from scripts.azureml.client import AzureMlSettings, build_ml_client
from scripts.azureml.config import load_release_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register Pricing MLOps Azure ML assets.")
    parser.add_argument(
        "--config",
        default="configs/azureml_auth_monitoring.yml",
        help="Path to Azure ML release config.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    config = load_release_config(repo_root / args.config, repo_root=repo_root)
    settings = AzureMlSettings.from_config(config)
    ml_client = build_ml_client(settings)

    print(f"Registering Azure ML environment from {config.environment.path.relative_to(repo_root)}")
    environment = load_environment(config.environment.path)
    ml_client.environments.create_or_update(environment)

    for component_file in config.components:
        print(f"Registering Azure ML component from {component_file.path.relative_to(repo_root)}")
        component = load_component(component_file.path)
        ml_client.components.create_or_update(component)

    print(f"Registering Azure ML pipeline component from {config.pipeline.path.relative_to(repo_root)}")
    pipeline_component = load_component(config.pipeline.path)
    ml_client.components.create_or_update(pipeline_component)

    print("Azure ML assets registered.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Replace shell wrapper**

Replace `scripts/register_azureml_components.sh` with:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

python "${REPO_ROOT}/scripts/azureml/register_assets.py" \
  --config "${AZURE_ML_RELEASE_CONFIG:-configs/azureml_auth_monitoring.yml}"
```

- [ ] **Step 5: Run tests**

Run:

```bash
python -m pytest tests/test_azureml_python_registration.py tests/test_azureml_component_specs.py -q
```

Expected: PASS after updating existing tests in Task 6 if they still assert CLI commands.

- [ ] **Step 6: Commit**

```bash
git add scripts/azureml/register_assets.py scripts/register_azureml_components.sh tests/test_azureml_python_registration.py
git commit -m "Register Azure ML assets with Python SDK"
```

---

### Task 5: Implement Python Endpoint Deployment

**Files:**
- Create: `scripts/azureml/deploy_endpoint.py`
- Modify: `scripts/deploy_auth_monitoring_batch_endpoint.sh`
- Modify: `tests/test_azureml_python_registration.py`

- [ ] **Step 1: Add tests for deployment script source**

Append to `tests/test_azureml_python_registration.py`:

```python
DEPLOY_ENDPOINT = ROOT / "scripts" / "azureml" / "deploy_endpoint.py"
DEPLOY_WRAPPER = ROOT / "scripts" / "deploy_auth_monitoring_batch_endpoint.sh"


def test_deploy_endpoint_uses_python_sdk_batch_clients():
    source = DEPLOY_ENDPOINT.read_text(encoding="utf-8")

    assert "load_batch_endpoint" in source
    assert "load_batch_deployment" in source
    assert "ml_client.batch_endpoints.begin_create_or_update" in source
    assert "ml_client.batch_deployments.begin_create_or_update" in source
    assert "az ml batch-deployment create" not in source


def test_deploy_shell_wrapper_delegates_to_python():
    source = DEPLOY_WRAPPER.read_text(encoding="utf-8")

    assert "python" in source
    assert "scripts/azureml/deploy_endpoint.py" in source
    assert "az ml batch-deployment create" not in source
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_azureml_python_registration.py::test_deploy_endpoint_uses_python_sdk_batch_clients tests/test_azureml_python_registration.py::test_deploy_shell_wrapper_delegates_to_python -q
```

Expected: FAIL because script is missing and wrapper still uses CLI.

- [ ] **Step 3: Implement Python deployment script**

Create `scripts/azureml/deploy_endpoint.py`:

```python
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import yaml
from azure.ai.ml import load_batch_deployment, load_batch_endpoint

from scripts.azureml.client import AzureMlSettings, build_ml_client
from scripts.azureml.config import load_release_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy Pricing MLOps AUTH monitoring batch endpoint.")
    parser.add_argument(
        "--config",
        default="configs/azureml_auth_monitoring.yml",
        help="Path to Azure ML release config.",
    )
    return parser.parse_args()


def _pipeline_component_from_manifest(manifest_path: Path) -> str:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    component = manifest.get("pipeline_component")
    if not isinstance(component, str) or not component.startswith("azureml:"):
        raise ValueError(f"Invalid pipeline_component in {manifest_path}")
    return component


def _render_deployment_file(source_file: Path, component_id: str) -> Path:
    data = yaml.safe_load(source_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Deployment YAML must be a mapping: {source_file}")
    data["component"] = component_id

    temp = tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False, encoding="utf-8")
    with temp:
        yaml.safe_dump(data, temp, sort_keys=False)
    return Path(temp.name)


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    config = load_release_config(repo_root / args.config, repo_root=repo_root)
    settings = AzureMlSettings.from_config(config)
    ml_client = build_ml_client(settings)

    pipeline_component = _pipeline_component_from_manifest(config.manifest.path)
    print(f"Creating/updating batch endpoint {config.endpoint.name}")
    endpoint = load_batch_endpoint(config.endpoint.endpoint_file.path)
    ml_client.batch_endpoints.begin_create_or_update(endpoint).result()

    print(f"Creating/updating batch deployment {config.endpoint.deployment} with {pipeline_component}")
    rendered_deployment = _render_deployment_file(config.endpoint.deployment_file.path, pipeline_component)
    try:
        deployment = load_batch_deployment(rendered_deployment)
        ml_client.batch_deployments.begin_create_or_update(deployment).result()
    finally:
        rendered_deployment.unlink(missing_ok=True)

    print(f"Batch endpoint ready: {config.endpoint.name}/{config.endpoint.deployment}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Replace shell wrapper**

Replace `scripts/deploy_auth_monitoring_batch_endpoint.sh` with:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

python "${REPO_ROOT}/scripts/azureml/deploy_endpoint.py" \
  --config "${AZURE_ML_RELEASE_CONFIG:-configs/azureml_auth_monitoring.yml}"
```

- [ ] **Step 5: Run tests**

Run:

```bash
python -m pytest tests/test_azureml_python_registration.py tests/test_batch_endpoint.py -q
```

Expected: PASS after updating legacy tests in Task 6 if they still assert CLI commands.

- [ ] **Step 6: Commit**

```bash
git add scripts/azureml/deploy_endpoint.py scripts/deploy_auth_monitoring_batch_endpoint.sh tests/test_azureml_python_registration.py
git commit -m "Deploy Azure ML endpoint with Python SDK"
```

---

### Task 6: Update Existing Contract Tests And GitHub Workflow

**Files:**
- Modify: `.github/workflows/azureml-components.yml`
- Modify: `tests/test_azureml_component_specs.py`
- Modify: `tests/test_batch_endpoint.py`
- Modify: `tests/test_auth_monitoring_pipeline_component.py`

- [ ] **Step 1: Update workflow tests to expect Python commands**

Edit tests that currently expect shell-only behavior so they assert:

```python
assert "python scripts/azureml/register_assets.py" in step_text
assert "python scripts/azureml/deploy_endpoint.py" in step_text
assert "scripts/invoke_auth_monitoring_batch_endpoint.sh" not in step_text
```

Keep existing assertions that push paths include Azure ML YAML files and do not include the smoke script.

- [ ] **Step 2: Update workflow commands**

In `.github/workflows/azureml-components.yml`, replace:

```yaml
run: scripts/register_azureml_components.sh
```

with:

```yaml
run: python scripts/azureml/register_assets.py --config configs/azureml_auth_monitoring.yml
```

Replace:

```yaml
run: scripts/deploy_auth_monitoring_batch_endpoint.sh
```

with:

```yaml
run: python scripts/azureml/deploy_endpoint.py --config configs/azureml_auth_monitoring.yml
```

- [ ] **Step 3: Run targeted tests**

Run:

```bash
python -m pytest tests/test_azureml_component_specs.py tests/test_batch_endpoint.py tests/test_auth_monitoring_pipeline_component.py tests/test_azureml_python_registration.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/azureml-components.yml tests/test_azureml_component_specs.py tests/test_batch_endpoint.py tests/test_auth_monitoring_pipeline_component.py
git commit -m "Use Python Azure ML deploy scripts in GitHub Actions"
```

---

### Task 7: Update Docs And Run Full Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/runbook.md`
- Modify: `docs/platform-contract.md`

- [ ] **Step 1: Update README commands**

Replace registration/deploy examples with:

```bash
AZURE_SUBSCRIPTION_ID=<subscription-id> \
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
python scripts/azureml/register_assets.py --config configs/azureml_auth_monitoring.yml
```

and:

```bash
AZURE_SUBSCRIPTION_ID=<subscription-id> \
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
python scripts/azureml/deploy_endpoint.py --config configs/azureml_auth_monitoring.yml
```

Keep the smoke command as local-only:

```bash
AZURE_RESOURCE_GROUP=<resource-group> \
AZURE_ML_WORKSPACE=<workspace> \
AZURE_STORAGE_ACCOUNT=<storage-account> \
AZURE_ML_JOB_IDENTITY_CLIENT_ID=<client-id> \
AZURE_ML_WAIT_FOR_COMPLETION=true \
scripts/invoke_auth_monitoring_batch_endpoint.sh
```

- [ ] **Step 2: Update runbook wording**

In `docs/runbook.md`, state:

```text
GitHub Actions uses Python SDK scripts to register Azure ML assets and update the batch endpoint. The shell scripts remain compatibility wrappers for local use. The smoke test remains local and is not part of GitHub Actions.
```

- [ ] **Step 3: Run full local verification**

Run:

```bash
python -m compileall src scripts tests
python -m pytest
python scripts/validate_inputs.py --input data/samples/masked/sample_pricing.csv
```

Expected:

```text
47 passed
validation passed: rows=3
```

- [ ] **Step 4: Run Azure registration/deploy dry operational verification**

Run against the real workspace only after local tests pass:

```bash
AZURE_SUBSCRIPTION_ID=a288ca29-947f-439f-8e5e-436f374b8a39 \
AZURE_RESOURCE_GROUP=rg-pricing-mlops-main \
AZURE_ML_WORKSPACE=mlw-pmlops-06152240 \
python scripts/azureml/register_assets.py --config configs/azureml_auth_monitoring.yml
```

Expected: existing assets are created or updated without errors.

Then run:

```bash
AZURE_SUBSCRIPTION_ID=a288ca29-947f-439f-8e5e-436f374b8a39 \
AZURE_RESOURCE_GROUP=rg-pricing-mlops-main \
AZURE_ML_WORKSPACE=mlw-pmlops-06152240 \
python scripts/azureml/deploy_endpoint.py --config configs/azureml_auth_monitoring.yml
```

Expected: `pricing-auth-monitoring/blue` remains ready and points to the manifest pipeline component.

- [ ] **Step 5: Do not run smoke in GitHub**

Verify workflow still excludes smoke:

```bash
rg -n "invoke_auth_monitoring_batch_endpoint|run_smoke" .github/workflows || true
```

Expected: no output.

- [ ] **Step 6: Commit**

```bash
git add README.md docs/runbook.md docs/platform-contract.md
git commit -m "Document Python Azure ML deployment flow"
```

---

## Final Verification Checklist

- [ ] `python -m compileall src scripts tests` passes.
- [ ] `python -m pytest` passes.
- [ ] `python scripts/validate_inputs.py --input data/samples/masked/sample_pricing.csv` passes.
- [ ] `python scripts/azureml/register_assets.py --config configs/azureml_auth_monitoring.yml` succeeds against Azure ML.
- [ ] `python scripts/azureml/deploy_endpoint.py --config configs/azureml_auth_monitoring.yml` succeeds against Azure ML.
- [ ] `rg -n "invoke_auth_monitoring_batch_endpoint|run_smoke" .github/workflows || true` returns no output.
- [ ] GitHub Actions push run succeeds.
- [ ] Local smoke remains available but is not part of GitHub Actions.

## Self-Review

- Spec coverage: The plan covers replacing CLI orchestration with Python SDK scripts, centralizing config, preserving YAML contracts, updating GitHub Actions, preserving local smoke, and documenting the new flow.
- Placeholder scan: No task uses TBD/TODO/fill-in-later language. Every code step includes concrete content or exact assertions.
- Type consistency: `ReleaseConfig`, `EndpointConfig`, `AssetFile`, and `AzureMlSettings` names are introduced before use and referenced consistently in later tasks.
