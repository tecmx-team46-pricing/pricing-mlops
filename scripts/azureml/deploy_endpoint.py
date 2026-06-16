from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml
from azure.ai.ml import load_batch_endpoint
from azure.ai.ml.entities import PipelineComponentBatchDeployment

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


def _load_pipeline_deployment(source_file: Path, component_id: str) -> PipelineComponentBatchDeployment:
    data = yaml.safe_load(source_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Deployment YAML must be a mapping: {source_file}")
    settings = data.get("settings")
    if not isinstance(settings, dict):
        raise ValueError(f"Pipeline deployment settings must be a mapping: {source_file}")

    return PipelineComponentBatchDeployment(
        name=data["name"],
        endpoint_name=data["endpoint_name"],
        component=component_id,
        settings=settings,
    )


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
    deployment = _load_pipeline_deployment(config.endpoint.deployment_file.path, pipeline_component)
    ml_client.batch_deployments.begin_create_or_update(deployment).result()

    print(f"Batch endpoint ready: {config.endpoint.name}/{config.endpoint.deployment}")


if __name__ == "__main__":
    main()
