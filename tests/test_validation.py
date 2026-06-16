import pytest

from pricing_mlops.preparation.validation import validate_pricing_input


def test_validates_required_columns_and_non_empty_dataset():
    frame = []

    with pytest.raises(ValueError, match="dataset is empty"):
        validate_pricing_input(frame)

    incomplete = [{"kpn": "KPN-001"}]

    with pytest.raises(ValueError, match="missing required columns"):
        validate_pricing_input(incomplete)


def test_validates_percentile_monotonicity_when_columns_exist():
    frame = [
        {
            "kpn": "KPN-001",
            "vpareadescription": "north",
            "distysegment": "enterprise",
            "current_price": 10.0,
            "P0_PRICE": 8.0,
            "P20_PRICE": 9.0,
            "P50_PRICE": 12.0,
            "P85_PRICE": 11.0,
            "P100_PRICE": 13.0,
        }
    ]

    with pytest.raises(ValueError, match="percentile prices must be monotonic"):
        validate_pricing_input(frame)


def test_validates_uniqueness_when_identity_columns_exist():
    frame = [
        {
            "kpn": "KPN-001",
            "vpareadescription": "north",
            "distysegment": "enterprise",
            "current_price": 10.0,
        },
        {
            "kpn": "KPN-001",
            "vpareadescription": "north",
            "distysegment": "enterprise",
            "current_price": 11.0,
        },
    ]

    with pytest.raises(ValueError, match="duplicate pricing keys"):
        validate_pricing_input(frame)


def test_accepts_valid_pricing_dataset():
    frame = [
        {
            "kpn": "KPN-001",
            "vpareadescription": "north",
            "distysegment": "enterprise",
            "current_price": 10.0,
            "P0_PRICE": 8.0,
            "P20_PRICE": 9.0,
            "P50_PRICE": 10.0,
            "P85_PRICE": 11.0,
            "P100_PRICE": 13.0,
        }
    ]

    result = validate_pricing_input(frame)

    assert result.row_count == 1
    assert result.status == "passed"
