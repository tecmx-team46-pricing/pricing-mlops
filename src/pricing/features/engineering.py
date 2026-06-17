from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


KEY_COLUMNS = ("kpn", "vpareadescription", "distysegment")
PRICE_COLUMNS = ("current_price", "rslpriceusd", "unit_price")
QUANTITY_COLUMNS = ("quantity", "quantity_sum", "qty")
REVENUE_COLUMNS = ("revenue_sum", "revenue", "extended_revenue")
PERCENTILE_COLUMNS = ("P20_PRICE", "P50_PRICE", "P85_PRICE")
OUTPUT_COLUMNS = (
    *KEY_COLUMNS,
    *PERCENTILE_COLUMNS,
    "n_transactions",
    "quantity_sum",
    "revenue_sum",
    "feature_engineering_run_id",
    "feature_schema_version",
)


@dataclass(frozen=True)
class FeatureEngineeringResult:
    current_auth_features_path: Path
    feature_table_path: Path
    row_count: int


def build_current_auth_features(
    input_path: str | Path,
    output_dir: str | Path,
    run_id: str,
) -> FeatureEngineeringResult:
    rows = _read_csv(Path(input_path))
    _require_columns(rows, KEY_COLUMNS)

    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = tuple(str(row[column]) for column in KEY_COLUMNS)
        grouped.setdefault(key, []).append(row)

    output_rows = [_build_feature_row(key, group, run_id) for key, group in grouped.items()]
    current_auth_features_path = Path(output_dir) / "curated" / "current_auth_features.csv"
    feature_table_path = Path(output_dir) / "curated" / "feature_table.csv"
    _write_csv(current_auth_features_path, output_rows)
    _write_csv(feature_table_path, output_rows)

    return FeatureEngineeringResult(
        current_auth_features_path=current_auth_features_path,
        feature_table_path=feature_table_path,
        row_count=len(output_rows),
    )


def _build_feature_row(
    key: tuple[str, str, str],
    rows: list[dict[str, str]],
    run_id: str,
) -> dict[str, object]:
    prices = [_first_float(row, PRICE_COLUMNS) for row in rows]
    prices = [price for price in prices if price is not None]
    quantity_sum = sum(_first_float(row, QUANTITY_COLUMNS) or 0.0 for row in rows)
    revenue_sum = sum(_row_revenue(row) for row in rows)

    return {
        "kpn": key[0],
        "vpareadescription": key[1],
        "distysegment": key[2],
        "P20_PRICE": _group_percentile(rows, prices, "P20_PRICE", 0.20),
        "P50_PRICE": _group_percentile(rows, prices, "P50_PRICE", 0.50),
        "P85_PRICE": _group_percentile(rows, prices, "P85_PRICE", 0.85),
        "n_transactions": len(rows),
        "quantity_sum": quantity_sum,
        "revenue_sum": revenue_sum,
        "feature_engineering_run_id": run_id,
        "feature_schema_version": "current_auth_features_v1",
    }


def _group_percentile(
    rows: list[dict[str, str]],
    prices: list[float],
    column: str,
    percentile: float,
) -> float | str:
    explicit = [_to_float(row.get(column)) for row in rows if row.get(column) not in (None, "")]
    explicit = [value for value in explicit if value is not None]
    if explicit:
        return explicit[0]
    if not prices:
        return ""
    return _percentile(prices, percentile)


def _row_revenue(row: dict[str, str]) -> float:
    explicit = _first_float(row, REVENUE_COLUMNS)
    if explicit is not None:
        return explicit
    price = _first_float(row, PRICE_COLUMNS) or 0.0
    quantity = _first_float(row, QUANTITY_COLUMNS) or 0.0
    return price * quantity


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = percentile * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def _first_float(row: dict[str, str], columns: tuple[str, ...]) -> float | None:
    for column in columns:
        value = _to_float(row.get(column))
        if value is not None:
            return value
    return None


def _to_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _require_columns(rows: list[dict[str, str]], required: tuple[str, ...]) -> None:
    columns = set(rows[0]) if rows else set()
    missing = [column for column in required if column not in columns]
    if missing:
        raise ValueError(f"feature engineering input is missing required columns: {missing}")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(OUTPUT_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
