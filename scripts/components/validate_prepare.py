#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from pricing_mlops.run import curate_pricing_records, read_csv_records, write_csv_records
from pricing_mlops.validation import validate_pricing_input
from scripts.run_azure_storage_flow import build_azure_credential


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate masked pricing input and prepare curated data.")
    parser.add_argument("--storage-account", required=True)
    parser.add_argument("--input-container", default="raw-masked")
    parser.add_argument("--input-blob-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--prepared-container", default="")
    parser.add_argument("--prepared-prefix", default="")
    args = parser.parse_args()

    try:
        run_component(
            storage_account=args.storage_account,
            input_container=args.input_container,
            input_blob_path=args.input_blob_path,
            output_dir=Path(args.output_dir),
            prepared_container=args.prepared_container,
            prepared_prefix=args.prepared_prefix,
        )
    except Exception as exc:
        print(f"validate_prepare failed: {exc}", file=sys.stderr)
        return 1
    return 0


def run_component(
    storage_account: str,
    input_container: str,
    input_blob_path: str,
    output_dir: Path,
    prepared_container: str = "",
    prepared_prefix: str = "",
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    input_path = output_dir / "input.csv"
    _download_blob(
        storage_account=storage_account,
        container=input_container,
        blob_path=input_blob_path,
        destination=input_path,
    )
    prepare_local_input(input_path=input_path, output_dir=output_dir, input_blob_path=input_blob_path)
    if prepared_container and prepared_prefix:
        _upload_files(
            storage_account=storage_account,
            container=prepared_container,
            blob_prefix=prepared_prefix,
            files=[output_dir / "curated_input.csv", output_dir / "validation_metadata.json"],
        )


def prepare_local_input(input_path: Path, output_dir: Path, input_blob_path: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_csv_records(input_path)
    validation = validate_pricing_input(rows)
    curated = curate_pricing_records(rows)

    write_csv_records(output_dir / "curated_input.csv", curated)
    (output_dir / "validation_metadata.json").write_text(
        json.dumps(
            {
                "input_blob_path": input_blob_path,
                "row_count": validation.row_count,
                "validation_status": validation.status,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _download_blob(storage_account: str, container: str, blob_path: str, destination: Path) -> None:
    from azure.storage.blob import BlobServiceClient

    account_url = f"https://{storage_account}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url=account_url, credential=build_azure_credential())
    blob = blob_service.get_blob_client(container=container, blob=blob_path)
    destination.write_bytes(blob.download_blob().readall())


def _upload_files(storage_account: str, container: str, blob_prefix: str, files: list[Path]) -> None:
    from azure.storage.blob import BlobServiceClient

    account_url = f"https://{storage_account}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url=account_url, credential=build_azure_credential())
    prefix = blob_prefix.strip("/")
    for file_path in files:
        blob_path = f"{prefix}/{file_path.name}" if prefix else file_path.name
        blob = blob_service.get_blob_client(container=container, blob=blob_path)
        with file_path.open("rb") as handle:
            blob.upload_blob(handle, overwrite=True)


if __name__ == "__main__":
    raise SystemExit(main())
