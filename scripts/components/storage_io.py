from __future__ import annotations

from pathlib import Path
import time


def download_blob(storage_account: str, container: str, blob_path: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    blob = _blob_service(storage_account).get_blob_client(container=container, blob=blob_path.strip("/"))
    destination.write_bytes(_download_with_retry(blob, blob_path))


def download_tree(storage_account: str, container: str, blob_prefix: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    blob_service = _blob_service(storage_account)
    prefix = blob_prefix.strip("/")
    blobs = list(blob_service.get_container_client(container).list_blobs(name_starts_with=f"{prefix}/"))
    if not blobs:
        raise FileNotFoundError(f"no artifacts found at {container}/{prefix}")
    for item in blobs:
        relative_path = item.name.removeprefix(f"{prefix}/")
        if not relative_path or relative_path == item.name:
            continue
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_download_with_retry(blob_service.get_blob_client(container, item.name), item.name))


def upload_tree(storage_account: str, container: str, blob_prefix: str, source: Path) -> None:
    blob_service = _blob_service(storage_account)
    prefix = blob_prefix.strip("/")
    for file_path in sorted(Path(source).rglob("*")):
        if not file_path.is_file():
            continue
        relative_path = file_path.relative_to(source).as_posix()
        blob = blob_service.get_blob_client(container=container, blob=f"{prefix}/{relative_path}")
        with file_path.open("rb") as handle:
            blob.upload_blob(handle, overwrite=True)


def _blob_service(storage_account: str):
    from azure.storage.blob import BlobServiceClient

    from scripts.azure_credentials import build_azure_credential

    return BlobServiceClient(
        account_url=f"https://{storage_account}.blob.core.windows.net",
        credential=build_azure_credential(),
    )


def _download_with_retry(blob, label: str, attempts: int = 60, delay_seconds: int = 10) -> bytes:
    for attempt in range(1, attempts + 1):
        try:
            return blob.download_blob().readall()
        except Exception as exc:
            if attempt == attempts:
                raise
            print(f"waiting for artifact: {label} attempt={attempt} error={exc}")
            time.sleep(delay_seconds)
    raise RuntimeError(f"artifact was not available: {label}")
