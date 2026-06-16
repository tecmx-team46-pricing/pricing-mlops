from pathlib import Path


def test_functional_artifact_contract_has_no_platform_dependency(tmp_path):
    from pricing.auth_monitoring import expected_auth_monitoring_artifacts
    from pricing_mlops.preparation import PREPARED_FILES

    assert tuple(PREPARED_FILES.values()) == ("curated_input.csv", "validation_metadata.json")
    assert "artifact_manifest" in expected_auth_monitoring_artifacts()


def test_domain_and_component_code_do_not_import_artifact_publishing():
    repo_root = Path(__file__).resolve().parents[1]
    checked_paths = [
        *sorted((repo_root / "src/pricing_mlops/preparation").glob("*.py")),
        repo_root / "scripts/components/validate_prepare.py",
        repo_root / "scripts/components/calculate_operational_decision.py",
    ]

    violations = [
        str(path.relative_to(repo_root))
        for path in checked_paths
        if "artifact_publishing" in path.read_text(encoding="utf-8")
    ]

    assert violations == []
