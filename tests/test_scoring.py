from pricing_mlops.scoring import score_pricing


def test_scoring_adds_controlled_recommendation_columns():
    frame = [
        {
            "kpn": "KPN-001",
            "vpareadescription": "north",
            "distysegment": "enterprise",
            "current_price": 10.0,
            "P50_PRICE": 12.0,
        }
    ]

    scored = score_pricing(frame)

    assert scored[0]["recommended_price"] == 12.0
    assert scored[0]["pricing_action"] == "review_increase"
    assert "score_timestamp_utc" in scored[0]
