from scripts.run_azure_storage_flow import build_azure_credential


def test_build_azure_credential_uses_obo_inside_aml_without_client_id(monkeypatch):
    monkeypatch.setenv("AZUREML_RUN_ID", "aml-run")
    monkeypatch.delenv("AZURE_CLIENT_ID", raising=False)

    credential = build_azure_credential()

    assert credential.__class__.__name__ == "AzureMLOnBehalfOfCredential"


def test_build_azure_credential_uses_default_credential_with_client_id(monkeypatch):
    monkeypatch.setenv("AZUREML_RUN_ID", "aml-run")
    monkeypatch.setenv("AZURE_CLIENT_ID", "managed-client-id")

    credential = build_azure_credential()

    assert credential.__class__.__name__ == "DefaultAzureCredential"
