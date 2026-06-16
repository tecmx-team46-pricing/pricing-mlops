from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class MaterializedMonitoringOutputs:
    output_root: Path
    files: dict[str, Path]

    @property
    def relative_paths(self) -> tuple[str, ...]:
        return tuple(self.files)


def materialize_monitoring_outputs(
    *,
    output_root: str | Path,
    snapshots: Mapping[str, Any] | None = None,
    logs: Mapping[str, Any] | None = None,
    summaries: Mapping[str, Any] | None = None,
    reports: Mapping[str, Any] | None = None,
) -> MaterializedMonitoringOutputs:
    """Write grouped monitoring artifacts under the local pipeline output root."""
    root = Path(output_root)
    groups = {
        "snapshots": snapshots or {},
        "logs": logs or {},
        "summaries": summaries or {},
        "reports": reports or {},
    }
    files = {
        f"{group_name}/{relative_name}": _write_materialized_output(
            root / group_name / _safe_relative_path(relative_name),
            payload,
        )
        for group_name, group_payloads in groups.items()
        for relative_name, payload in group_payloads.items()
    }
    return MaterializedMonitoringOutputs(output_root=root, files=files)


def write_artifact_manifest(root: str | Path, run_id: str) -> Path:
    root = Path(root)
    manifest_dir = root / "manifest"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    records = [
        {
            "run_id": run_id,
            "logical_name": _logical_name(path.relative_to(root)),
            "relative_path": path.relative_to(root).as_posix(),
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.parent != manifest_dir
    ]
    manifest_path = manifest_dir / "artifact_manifest.json"
    manifest_path.write_text(
        json.dumps({"schema_version": "auth_monitoring_artifact_manifest_v1", "artifacts": records}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _logical_name(relative_path: Path) -> str:
    return relative_path.with_suffix("").as_posix().replace("/", "_")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative_path(relative_name: str) -> Path:
    path = Path(relative_name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Artifact path must stay relative to its output group: {relative_name}")
    return path


def _write_materialized_output(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(payload, "to_csv"):
        payload.to_csv(path, index=False)
        return path
    if isinstance(payload, bytes):
        path.write_bytes(payload)
        return path
    path.write_text(str(payload), encoding="utf-8")
    return path
