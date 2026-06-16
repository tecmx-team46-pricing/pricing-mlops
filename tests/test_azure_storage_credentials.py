from scripts.azure_credentials import build_azure_credential


def test_build_azure_credential_uses_obo_inside_aml_without_client_id(monkeypatch):
    monkeypatch.setenv("AZUREML_RUN_ID", "aml-run")
    monkeypatch.delenv("AZURE_CLIENT_ID", raising=False)

    credential = build_azure_credential()

    assert credential.__class__.__name__ == "AzureMLOnBehalfOfCredential"


def test_build_azure_credential_still_uses_obo_inside_aml_with_client_id(monkeypatch):
    monkeypatch.setenv("AZUREML_RUN_ID", "aml-run")
    monkeypatch.setenv("AZURE_CLIENT_ID", "managed-client-id")

    credential = build_azure_credential()

    assert credential.__class__.__name__ == "AzureMLOnBehalfOfCredential"


def test_build_azure_credential_uses_managed_identity_when_requested(monkeypatch):
    monkeypatch.setenv("AZUREML_RUN_ID", "aml-run")
    monkeypatch.setenv("AZURE_ML_JOB_IDENTITY_CLIENT_ID", "managed-client-id")
    monkeypatch.setenv("MLOPS_USE_MANAGED_IDENTITY_CREDENTIAL", "true")

    credential = build_azure_credential()

    assert credential.__class__.__name__ == "ManagedIdentityCredential"


def test_build_azure_credential_can_force_default_credential(monkeypatch):
    monkeypatch.setenv("AZUREML_RUN_ID", "aml-run")
    monkeypatch.setenv("AZURE_CLIENT_ID", "managed-client-id")
    monkeypatch.setenv("MLOPS_FORCE_DEFAULT_CREDENTIAL", "true")

    credential = build_azure_credential()

    assert credential.__class__.__name__ == "DefaultAzureCredential"
