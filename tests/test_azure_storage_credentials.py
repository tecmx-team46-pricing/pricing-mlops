from scripts.run_azure_storage_flow import build_azure_credential


def test_build_azure_credential_uses_default_credential_inside_aml(monkeypatch):
    monkeypatch.setenv("AZUREML_RUN_ID", "aml-run")

    credential = build_azure_credential()

    assert credential.__class__.__name__ == "DefaultAzureCredential"
