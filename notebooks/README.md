# Notebooks

Use this directory for controlled notebooks only.

Recommended naming convention:

```text
<number>-<initials>-<short-description>.ipynb
```

Examples:

```text
01-ds-pricing-input-review.ipynb
02-ds-drift-threshold-check.ipynb
```

Rules:

- Do not commit notebooks with unmasked data outputs.
- Clear outputs before committing unless the output is synthetic and useful for review.
- Keep exploratory or historical EDA in `pricing-mlops-eda` unless it is needed for the operational flow.
- Operational Azure ML should execute components from `scripts/components/`, not full notebooks as black-box runtime.
- Keep `auth_recommendation_monitoring_pipeline_abstraction.ipynb` aligned with `src/pricing/auth_monitoring/` and replace inline constants with `auth_monitoring_config.json`.
- Use `PIPELINE_MONITORING_CONFIG` as the official pipeline contract and `EXPERIMENTAL_THRESHOLDS` only for experimental notebook overrides. See [`../docs/auth-monitoring-configuration.md`](../docs/auth-monitoring-configuration.md).
