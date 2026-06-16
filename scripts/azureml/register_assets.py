from __future__ import annotations

import argparse
import sys
from pathlib import Path

from azure.ai.ml import load_component, load_environment
from azure.core.exceptions import ResourceNotFoundError

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

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


def _component_exists(ml_client, component) -> bool:
    try:
        ml_client.components.get(name=component.name, version=component.version)
    except ResourceNotFoundError:
        return False
    return True


def _register_component(ml_client, component, *, label: str) -> None:
    component_ref = f"{component.name}:{component.version}"
    if _component_exists(ml_client, component):
        print(f"Azure ML {label} already exists: {component_ref}")
        return
    ml_client.components.create_or_update(component)


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
        _register_component(ml_client, component, label="component")

    print(f"Registering Azure ML pipeline component from {config.pipeline.path.relative_to(repo_root)}")
    pipeline_component = load_component(config.pipeline.path)
    _register_component(ml_client, pipeline_component, label="pipeline component")

    print("Azure ML assets registered.")


if __name__ == "__main__":
    main()
