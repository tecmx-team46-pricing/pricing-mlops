from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class SinkConfig:
    name: str
    enabled: bool = True
    required: bool = True


@dataclass(frozen=True)
class PublishingConfig:
    sinks: tuple[SinkConfig, ...]
    containers: dict[str, str]

    @classmethod
    def from_env(cls) -> PublishingConfig:
        enabled_sinks = _csv_env("MLOPS_ARTIFACT_SINKS", default=("azure_blob",))
        optional_sinks = set(_csv_env("MLOPS_OPTIONAL_ARTIFACT_SINKS", default=("azure_ml", "sql_metadata")))
        return cls(
            sinks=tuple(
                SinkConfig(
                    name=sink,
                    enabled=True,
                    required=sink not in optional_sinks,
                )
                for sink in enabled_sinks
            ),
            containers={
                "curated": os.getenv("MLOPS_CONTAINER_CURATED", "curated"),
                "runs": os.getenv("MLOPS_CONTAINER_RUNS", "runs"),
                "snapshots": os.getenv("MLOPS_CONTAINER_SNAPSHOTS", "snapshots"),
                "drift_logs": os.getenv("MLOPS_CONTAINER_DRIFT_LOGS", "drift-logs"),
                "reports": os.getenv("MLOPS_CONTAINER_REPORTS", "reports"),
                "artifacts": os.getenv("MLOPS_CONTAINER_ARTIFACTS", "artifacts"),
            },
        )

    def enabled_sink_names(self) -> tuple[str, ...]:
        return tuple(sink.name for sink in self.sinks if sink.enabled)

    def is_required(self, sink_name: str) -> bool:
        return next((sink.required for sink in self.sinks if sink.name == sink_name), False)


def _csv_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw_value = os.getenv(name)
    if not raw_value:
        return default
    return tuple(value.strip() for value in raw_value.split(",") if value.strip())
