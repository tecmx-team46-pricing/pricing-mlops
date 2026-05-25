from pathlib import Path


FORBIDDEN_INFRASTRUCTURE_IMPORTS = (
    "azure.",
    "azureml",
    "sqlalchemy",
    "pyodbc",
    "BlobServiceClient",
    "TableServiceClient",
    "MLClient",
    "DefaultAzureCredential",
    "connection_string",
    "account_key",
)


def test_domain_modules_do_not_import_infrastructure_sdks():
    repo_root = Path(__file__).resolve().parents[1]
    domain_files = [
        repo_root / "src/pricing_mlops/scoring.py",
        repo_root / "src/pricing_mlops/drift.py",
        repo_root / "src/pricing_mlops/validation.py",
        repo_root / "src/pricing_mlops/run.py",
    ]

    violations = {
        str(path.relative_to(repo_root)): token
        for path in domain_files
        for token in FORBIDDEN_INFRASTRUCTURE_IMPORTS
        if token in path.read_text(encoding="utf-8")
    }

    assert violations == {}
