from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import yaml
from azure.ai.ml import load_batch_deployment, load_batch_endpoint

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

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
