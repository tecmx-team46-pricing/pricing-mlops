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
