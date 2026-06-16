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
