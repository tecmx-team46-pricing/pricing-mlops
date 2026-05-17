from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class PlatformConfig:
    environment: str | None
    storage_account: str | None
    storage_dfs_endpoint: str | None
    key_vault_uri: str | None
    raw_masked_container: str | None
    curated_container: str | None
    baseline_container: str | None
    runs_container: str | None
    snapshots_container: str | None
    drift_logs_container: str | None
    reports_container: str | None
    artifacts_container: str | None


def load_dotenv(path: str | Path) -> dict[str, str]:
    values: dict[str, str] = {}
    env_path = Path(path)
    if not env_path.exists():
        raise FileNotFoundError(f"env file not found: {env_path}")

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def platform_config_from_env() -> PlatformConfig:
    return PlatformConfig(
        environment=os.getenv("MLOPS_ENVIRONMENT"),
        storage_account=os.getenv("AZURE_STORAGE_ACCOUNT"),
        storage_dfs_endpoint=os.getenv("AZURE_STORAGE_DFS_ENDPOINT"),
        key_vault_uri=os.getenv("AZURE_KEY_VAULT_URI"),
        raw_masked_container=os.getenv("MLOPS_CONTAINER_RAW_MASKED"),
        curated_container=os.getenv("MLOPS_CONTAINER_CURATED"),
        baseline_container=os.getenv("MLOPS_CONTAINER_BASELINE"),
        runs_container=os.getenv("MLOPS_CONTAINER_RUNS"),
        snapshots_container=os.getenv("MLOPS_CONTAINER_SNAPSHOTS"),
        drift_logs_container=os.getenv("MLOPS_CONTAINER_DRIFT_LOGS"),
        reports_container=os.getenv("MLOPS_CONTAINER_REPORTS"),
        artifacts_container=os.getenv("MLOPS_CONTAINER_ARTIFACTS"),
    )
