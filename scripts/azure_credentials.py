from __future__ import annotations

import os


def build_azure_credential():
    if os.getenv("MLOPS_USE_MANAGED_IDENTITY_CREDENTIAL", "").lower() == "true":
        from azure.identity import ManagedIdentityCredential

        client_id = os.getenv("AZURE_ML_JOB_IDENTITY_CLIENT_ID") or None
        return ManagedIdentityCredential(client_id=client_id)
    if os.getenv("AZUREML_RUN_ID") and os.getenv("MLOPS_FORCE_DEFAULT_CREDENTIAL", "").lower() != "true":
        from azure.ai.ml.identity import AzureMLOnBehalfOfCredential

        return AzureMLOnBehalfOfCredential()
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential(exclude_interactive_browser_credential=True)
