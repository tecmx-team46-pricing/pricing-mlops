from __future__ import annotations

import csv
from pathlib import Path


PREPARED_FILES = {
    "curated_input": "curated_input.csv",
    "validation_metadata": "validation_metadata.json",
}


def read_csv_records(path: str | Path) -> list[dict[str, str]]:
    csv_path = Path(path)
    with csv_path.open(newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def curate_pricing_records(records: list[dict[str, str]]) -> list[dict[str, object]]:
    numeric_columns = (
        "current_price",
        "rslpriceusd",
        "quantity",
        "P0_PRICE",
        "P20_PRICE",
        "P50_PRICE",
        "P85_PRICE",
        "P100_PRICE",
    )
    curated: list[dict[str, object]] = []
    for record in records:
        row: dict[str, object] = {}
        for key, value in record.items():
            normalized_key = key.strip()
            if normalized_key in numeric_columns:
                row[normalized_key] = _to_float(value)
            else:
                row[normalized_key] = value.strip() if isinstance(value, str) else value
        if "current_price" not in row and "rslpriceusd" in row:
            row["current_price"] = row["rslpriceusd"]
        curated.append(row)
    return curated


def write_csv_records(path: str | Path, records: list[dict[str, object]]) -> None:
    output_path = Path(path)
    if not records:
        output_path.write_text("")
        return

    fieldnames = list(records[0].keys())
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
