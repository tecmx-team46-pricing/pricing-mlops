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

FORBIDDEN_TEMPORARY_MONITORING_PATHS = (
    Path("src/pricing_mlops/monitoring/domain"),
    Path("src/pricing_mlops/monitoring/steps"),
    Path("src/pricing_mlops/monitoring/config.py"),
    Path("src/pricing_mlops/monitoring/artifact_contract.py"),
)

FORBIDDEN_UNUSED_MLOPS_ROOT_MODULES = (
    Path("src/pricing_mlops/config.py"),
    Path("src/pricing_mlops/types.py"),
)

FORBIDDEN_LEGACY_MONITORING_IMPORTS = (
    ".".join(("pricing_mlops", "monitoring", "domain", "notebook_logic")),
    ".".join(("pricing_mlops", "monitoring", "steps")),
    ".".join(("pricing_mlops", "monitoring", "config")),
    ".".join(("pricing_mlops", "monitoring", "artifact_contract")),
)

FORBIDDEN_MODEL_REPO_WORKFLOW_TOKENS = (
    "azure/login",
    "run_azure_flow",
    "run_model_flow_function.sh",
    "AZURE_FUNCTION_APP",
    "AZURE_ML_WORKSPACE",
    "tecmx-team46-pricing/pricing-mlops-platform",
)


def test_domain_modules_do_not_import_infrastructure_sdks():
    repo_root = Path(__file__).resolve().parents[1]
    domain_files = sorted((repo_root / "src" / "pricing").rglob("*.py"))

    violations = {
        str(path.relative_to(repo_root)): token
        for path in domain_files
        for token in FORBIDDEN_INFRASTRUCTURE_IMPORTS
        if token in path.read_text(encoding="utf-8")
    }

    assert violations == {}


def test_pricing_domain_does_not_import_mlops_runtime():
    repo_root = Path(__file__).resolve().parents[1]
    domain_files = sorted((repo_root / "src" / "pricing").rglob("*.py"))

    violations = [
        str(path.relative_to(repo_root))
        for path in domain_files
        if "pricing_mlops" in path.read_text(encoding="utf-8")
    ]

    assert violations == []


def test_mlops_runtime_modules_do_not_import_infrastructure_sdks():
    repo_root = Path(__file__).resolve().parents[1]
    runtime_files = sorted((repo_root / "src" / "pricing_mlops").rglob("*.py"))

    violations = {
        str(path.relative_to(repo_root)): token
        for path in runtime_files
        for token in FORBIDDEN_INFRASTRUCTURE_IMPORTS
        if token in path.read_text(encoding="utf-8")
    }

    assert violations == {}


def test_removed_monitoring_compatibility_paths_stay_removed():
    repo_root = Path(__file__).resolve().parents[1]

    existing_paths = [
        path.as_posix()
        for path in FORBIDDEN_TEMPORARY_MONITORING_PATHS
        if (repo_root / path).exists()
    ]

    assert existing_paths == []


def test_removed_mlops_root_placeholders_stay_removed():
    repo_root = Path(__file__).resolve().parents[1]

    existing_paths = [
        path.as_posix()
        for path in FORBIDDEN_UNUSED_MLOPS_ROOT_MODULES
        if (repo_root / path).exists()
    ]

    assert existing_paths == []


def test_old_monitoring_imports_are_not_reintroduced():
    repo_root = Path(__file__).resolve().parents[1]
    checked_roots = [
        repo_root / "src",
        repo_root / "scripts",
        repo_root / "tests",
        repo_root / "notebooks",
        repo_root / "docs",
    ]
    checked_files = [
        path
        for root in checked_roots
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
        and path.name != "test_architecture_boundaries.py"
    ] + [repo_root / "README.md"]

    violations = {
        str(path.relative_to(repo_root)): token
        for path in checked_files
        for token in FORBIDDEN_LEGACY_MONITORING_IMPORTS
        if token in path.read_text(encoding="utf-8", errors="ignore")
    }

    assert violations == {}


def test_model_repo_workflows_do_not_operate_azure_flow():
    repo_root = Path(__file__).resolve().parents[1]
    workflow_files = sorted((repo_root / ".github" / "workflows").glob("*.yml"))

    violations = {
        str(path.relative_to(repo_root)): token
        for path in workflow_files
        for token in FORBIDDEN_MODEL_REPO_WORKFLOW_TOKENS
        if token in path.read_text(encoding="utf-8", errors="ignore")
    }

    assert violations == {}


def test_platform_environment_examples_are_not_reintroduced():
    repo_root = Path(__file__).resolve().parents[1]
    environment_dir = repo_root / "configs" / "environments"
    environment_examples = sorted(environment_dir.glob("*." + "example" + ".env"))

    assert [path.as_posix() for path in environment_examples] == []
