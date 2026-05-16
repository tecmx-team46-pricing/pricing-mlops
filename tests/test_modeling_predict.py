from pricing_mlops.modeling.predict import score_pricing


def test_modeling_predict_exposes_scoring_api():
    scored = score_pricing(
        [
            {
                "kpn": "KPN-001",
                "vpareadescription": "north",
                "distysegment": "enterprise",
                "current_price": 10.0,
                "P50_PRICE": 12.0,
            }
        ]
    )

    assert scored[0]["recommended_price"] == 12.0
    assert scored[0]["pricing_action"] == "review_increase"
