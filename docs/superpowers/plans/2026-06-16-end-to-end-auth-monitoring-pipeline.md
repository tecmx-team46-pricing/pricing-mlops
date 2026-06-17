# End-to-End AUTH Monitoring Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the current AUTH monitoring pipeline so it can build its own current AUTH history snapshot, optionally build/refresh the baseline snapshot, and move from a monitoring MVP toward the original MLOps flow.

**Architecture:** Keep the current Azure ML component pattern: small command components wrapping testable Python modules. Add upstream data-preparation components before `build_monitoring_inputs`, then replace simulated handoff with real scoring/handoff only after monitoring remains stable. Storage remains the functional contract boundary.

**Tech Stack:** Python stdlib CSV utilities, existing `pricing_mlops` modules, Azure ML component YAML, pytest, Azure Blob Storage via existing component wrappers.

---

## File Structure

- Create `src/pricing_mlops/monitoring/pipeline/steps/prepare_current_auth_history.py`
  - Builds `snapshots/current_auth_history_snapshot_real.csv` from curated or raw masked AUTH records.
- Create `scripts/components/prepare_current_auth_history.py`
  - Azure ML component entrypoint; downloads input CSV and writes the current history snapshot.
- Create `azureml/components/prepare_current_auth_history.yml`
  - Azure ML command component spec.
- Modify `src/pricing_mlops/monitoring/pipeline/registry.py`
  - Registers the new step and state paths.
- Modify `azureml/pipelines/auth_monitoring_pipeline.yml`
  - Wires `validate_prepare -> prepare_current_auth_history -> build_monitoring_inputs`.
- Modify `configs/azureml_auth_monitoring.yml`
  - Adds component registration.
- Add `tests/test_prepare_current_auth_history.py`
  - Unit tests for aggregation and output schema.
- Add `tests/test_prepare_current_auth_history_component.py`
  - Component entrypoint tests.
- Modify `tests/test_auth_monitoring_pipeline_component.py`
  - Verifies new job exists and dependencies are ordered.
- Modify `docs/platform-contract.md`, `docs/compute-target-contract.md`, and `README.md`
  - Documents the new end-to-end flow and remaining gaps.

Later tasks create:

- `src/pricing/baseline/build_snapshot.py`
- `scripts/components/build_baseline_snapshot.py`
- `azureml/components/build_baseline_snapshot.yml`
- `src/pricing/scoring/recommendations.py`
- `scripts/components/score_recommendations.py`
- `azureml/components/score_recommendations.yml`

---

### Task 1: Add Current AUTH History Builder

**Files:**
- Create: `src/pricing_mlops/monitoring/pipeline/steps/prepare_current_auth_history.py`
- Test: `tests/test_prepare_current_auth_history.py`

- [ ] **Step 1: Write failing aggregation tests**

Create `tests/test_prepare_current_auth_history.py`:

```python
from pathlib import Path

from pricing_mlops.monitoring.pipeline.steps.prepare_current_auth_history import (
    prepare_current_auth_history,
)


def write_csv(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def test_prepare_current_auth_history_aggregates_by_monitoring_key(tmp_path):
    input_path = tmp_path / "curated_input.csv"
    output_dir = tmp_path / "out"
    write_csv(
        input_path,
        """
kpn,vpareadescription,distysegment,current_price,quantity,revenue_sum,P20_PRICE,P50_PRICE,P85_PRICE
KPN_1,VP_1,SEG_1,10,2,20,8,10,12
KPN_1,VP_1,SEG_1,14,1,14,8,10,12
KPN_2,VP_1,SEG_1,5,3,15,4,5,6
""",
    )

    result = prepare_current_auth_history(input_path, output_dir, run_id="run-1")

    output_path = output_dir / "snapshots" / "current_auth_history_snapshot_real.csv"
    rows = output_path.read_text(encoding="utf-8").splitlines()
    assert result.row_count == 2
    assert rows[0].split(",") == [
        "kpn",
        "vpareadescription",
        "distysegment",
        "P20_PRICE",
        "P50_PRICE",
        "P85_PRICE",
        "n_transactions",
        "quantity_sum",
        "revenue_sum",
        "current_history_run_id",
        "history_snapshot_type",
    ]
    assert "KPN_1,VP_1,SEG_1,8,10,12,2,3.0,34.0,run-1,current_auth_history_real" in rows


def test_prepare_current_auth_history_rejects_missing_keys(tmp_path):
    input_path = tmp_path / "curated_input.csv"
    output_dir = tmp_path / "out"
    write_csv(input_path, "kpn,current_price\nKPN_1,10")

    try:
        prepare_current_auth_history(input_path, output_dir, run_id="run-1")
    except ValueError as exc:
        assert "missing required columns" in str(exc)
    else:
        raise AssertionError("expected ValueError")
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd /Users/me/Developer/tecmx-team46-pricing/pricing-mlops
python -m pytest tests/test_prepare_current_auth_history.py -v
```

Expected: FAIL with `ModuleNotFoundError` or missing function.

- [ ] **Step 3: Implement minimal builder**

Create `src/pricing_mlops/monitoring/pipeline/steps/prepare_current_auth_history.py`:

```python
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


KEY_COLUMNS = ("kpn", "vpareadescription", "distysegment")
PERCENTILE_COLUMNS = ("P20_PRICE", "P50_PRICE", "P85_PRICE")


@dataclass(frozen=True)
class CurrentAuthHistoryResult:
    output_path: Path
    row_count: int


def prepare_current_auth_history(input_path: str | Path, output_dir: str | Path, run_id: str) -> CurrentAuthHistoryResult:
    rows = _read_csv(Path(input_path))
    _require_columns(rows, [*KEY_COLUMNS, *PERCENTILE_COLUMNS])

    grouped: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in rows:
        key = tuple(str(row[column]) for column in KEY_COLUMNS)
        target = grouped.setdefault(
            key,
            {
                "kpn": key[0],
                "vpareadescription": key[1],
                "distysegment": key[2],
                "P20_PRICE": row.get("P20_PRICE", ""),
                "P50_PRICE": row.get("P50_PRICE", ""),
                "P85_PRICE": row.get("P85_PRICE", ""),
                "n_transactions": 0,
                "quantity_sum": 0.0,
                "revenue_sum": 0.0,
                "current_history_run_id": run_id,
                "history_snapshot_type": "current_auth_history_real",
            },
        )
        target["n_transactions"] = int(target["n_transactions"]) + 1
        target["quantity_sum"] = float(target["quantity_sum"]) + _to_float(row.get("quantity"))
        target["revenue_sum"] = float(target["revenue_sum"]) + _to_float(row.get("revenue_sum"))

    output_path = Path(output_dir) / "snapshots" / "current_auth_history_snapshot_real.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(output_path, list(grouped.values()))
    return CurrentAuthHistoryResult(output_path=output_path, row_count=len(grouped))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _require_columns(rows: list[dict[str, str]], required: list[str]) -> None:
    columns = set(rows[0]) if rows else set()
    missing = [column for column in required if column not in columns]
    if missing:
        raise ValueError(f"current AUTH history input is missing required columns: {missing}")


def _to_float(value: object) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "kpn",
        "vpareadescription",
        "distysegment",
        "P20_PRICE",
        "P50_PRICE",
        "P85_PRICE",
        "n_transactions",
        "quantity_sum",
        "revenue_sum",
        "current_history_run_id",
        "history_snapshot_type",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
```

- [ ] **Step 4: Run test to verify pass**

Run:

```bash
cd /Users/me/Developer/tecmx-team46-pricing/pricing-mlops
python -m pytest tests/test_prepare_current_auth_history.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pricing_mlops/monitoring/pipeline/steps/prepare_current_auth_history.py tests/test_prepare_current_auth_history.py
git commit -m "feat: build current auth history snapshot"
```

---

### Task 2: Add Azure ML Component Entrypoint

**Files:**
- Create: `scripts/components/prepare_current_auth_history.py`
- Create: `azureml/components/prepare_current_auth_history.yml`
- Test: `tests/test_prepare_current_auth_history_component.py`

- [ ] **Step 1: Write component test**

Create `tests/test_prepare_current_auth_history_component.py`:

```python
from pathlib import Path

from scripts.components.prepare_current_auth_history import prepare_local_current_history


def test_prepare_local_current_history_writes_snapshot(tmp_path):
    input_path = tmp_path / "curated_input.csv"
    output_dir = tmp_path / "outputs"
    input_path.write_text(
        "kpn,vpareadescription,distysegment,P20_PRICE,P50_PRICE,P85_PRICE,quantity,revenue_sum\n"
        "KPN_1,VP_1,SEG_1,8,10,12,2,20\n",
        encoding="utf-8",
    )

    prepare_local_current_history(input_path=input_path, output_dir=output_dir, run_id="run-1")

    assert (output_dir / "snapshots" / "current_auth_history_snapshot_real.csv").exists()
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd /Users/me/Developer/tecmx-team46-pricing/pricing-mlops
python -m pytest tests/test_prepare_current_auth_history_component.py -v
```

Expected: FAIL with missing script.

- [ ] **Step 3: Implement component script**

Create `scripts/components/prepare_current_auth_history.py`:

```python
#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from pricing_mlops.monitoring.pipeline.steps.prepare_current_auth_history import prepare_current_auth_history
from scripts.components.storage_io import download_blob, upload_tree


def main() -> int:
    parser = argparse.ArgumentParser(description="Build current AUTH history snapshot from curated pricing input.")
    parser.add_argument("--storage-account", required=True)
    parser.add_argument("--input-container", default="raw-masked")
    parser.add_argument("--input-blob-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--current-history-container", default="")
    parser.add_argument("--current-history-prefix", default="")
    args = parser.parse_args()

    try:
        input_path = Path(args.output_dir) / "current_history_input.csv"
        download_blob(args.storage_account, args.input_container, args.input_blob_path, input_path)
        prepare_local_current_history(input_path=input_path, output_dir=Path(args.output_dir), run_id=args.run_id)
        if args.current_history_container and args.current_history_prefix:
            upload_tree(args.storage_account, args.current_history_container, args.current_history_prefix, Path(args.output_dir))
    except Exception as exc:
        print(f"prepare_current_auth_history failed: {exc}", file=sys.stderr)
        return 1
    return 0


def prepare_local_current_history(input_path: Path, output_dir: Path, run_id: str) -> None:
    prepare_current_auth_history(input_path=input_path, output_dir=output_dir, run_id=run_id)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Add Azure ML component spec**

Create `azureml/components/prepare_current_auth_history.yml`:

```yaml
$schema: https://azuremlschemas.azureedge.net/latest/commandComponent.schema.json
type: command
name: pricing_mlops_prepare_current_auth_history
version: 0.1.0
display_name: prepare_current_auth_history
description: Build current AUTH history snapshot from masked or curated AUTH input.
inputs:
  storage_account:
    type: string
  input_container:
    type: string
    default: raw-masked
  input_blob_path:
    type: string
  run_id:
    type: string
  current_history_container:
    type: string
    default: artifacts
  current_history_prefix:
    type: string
    default: component-state/current-auth-history
outputs:
  flow_token:
    type: uri_folder
code: ../../
environment: azureml:pricing-mlops-env:0.1.0
command: >-
  python scripts/components/prepare_current_auth_history.py
  --storage-account ${{inputs.storage_account}}
  --input-container ${{inputs.input_container}}
  --input-blob-path ${{inputs.input_blob_path}}
  --output-dir outputs
  --run-id ${{inputs.run_id}}
  --current-history-container ${{inputs.current_history_container}}
  --current-history-prefix ${{inputs.current_history_prefix}}/${{inputs.run_id}}
  && mkdir -p ${{outputs.flow_token}}
  && echo prepare_current_auth_history > ${{outputs.flow_token}}/done.txt
```

- [ ] **Step 5: Run tests**

Run:

```bash
cd /Users/me/Developer/tecmx-team46-pricing/pricing-mlops
python -m pytest tests/test_prepare_current_auth_history_component.py tests/test_azureml_component_specs.py -v
```

Expected: PASS. If `test_azureml_component_specs.py` enforces a component allowlist, update that allowlist to include `azureml/components/prepare_current_auth_history.yml`.

- [ ] **Step 6: Commit**

```bash
git add scripts/components/prepare_current_auth_history.py azureml/components/prepare_current_auth_history.yml tests/test_prepare_current_auth_history_component.py tests/test_azureml_component_specs.py
git commit -m "feat: add current auth history component"
```

---

### Task 3: Wire Current History Into Pipeline

**Files:**
- Modify: `azureml/pipelines/auth_monitoring_pipeline.yml`
- Modify: `configs/azureml_auth_monitoring.yml`
- Modify: `tests/test_auth_monitoring_pipeline_component.py`
- Modify: `azureml/manifests/auth-monitoring-release.json`

- [ ] **Step 1: Write failing pipeline test**

Modify `tests/test_auth_monitoring_pipeline_component.py` to assert:

```python
def test_pipeline_prepares_current_history_before_monitoring_inputs():
    pipeline = load_pipeline()
    assert "prepare_current_auth_history" in pipeline["jobs"]
    build_inputs = pipeline["jobs"]["build_monitoring_inputs"]["inputs"]
    assert (
        build_inputs["previous_step_token"]["path"]
        == "${{parent.jobs.prepare_current_auth_history.outputs.flow_token}}"
    )
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd /Users/me/Developer/tecmx-team46-pricing/pricing-mlops
python -m pytest tests/test_auth_monitoring_pipeline_component.py -v
```

Expected: FAIL because the job is not wired.

- [ ] **Step 3: Add pipeline job**

In `azureml/pipelines/auth_monitoring_pipeline.yml`, insert after `validate_prepare`:

```yaml
  prepare_current_auth_history:
    type: command
    compute: azureml:cpu-cluster
    component: azureml:pricing_mlops_prepare_current_auth_history:0.1.0
    inputs:
      storage_account: ${{parent.inputs.storage_account}}
      input_container: raw-masked
      input_blob_path: ${{parent.inputs.current_history_blob_path}}
      run_id: ${{parent.inputs.run_id}}
      current_history_container: artifacts
      current_history_prefix: component-state/current-auth-history
      previous_step_token:
        type: uri_folder
        path: ${{parent.jobs.validate_prepare.outputs.flow_token}}
    outputs:
      flow_token:
        type: uri_folder
    identity:
      type: managed_identity
```

Then change `build_monitoring_inputs.inputs.previous_step_token.path` to:

```yaml
path: ${{parent.jobs.prepare_current_auth_history.outputs.flow_token}}
```

Set `build_monitoring_inputs.inputs.current_history_container` to `artifacts` and `current_history_blob_path` to:

```yaml
component-state/current-auth-history/${{parent.inputs.run_id}}/snapshots/current_auth_history_snapshot_real.csv
```

- [ ] **Step 4: Register component in config and manifest**

In `configs/azureml_auth_monitoring.yml`, add:

```yaml
  - azureml/components/prepare_current_auth_history.yml
```

In `azureml/manifests/auth-monitoring-release.json`, add:

```json
"prepare_current_auth_history": "azureml:pricing_mlops_prepare_current_auth_history:0.1.0"
```

- [ ] **Step 5: Run tests**

Run:

```bash
cd /Users/me/Developer/tecmx-team46-pricing/pricing-mlops
python -m pytest tests/test_auth_monitoring_pipeline_component.py tests/test_azureml_python_registration.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add azureml/pipelines/auth_monitoring_pipeline.yml configs/azureml_auth_monitoring.yml azureml/manifests/auth-monitoring-release.json tests/test_auth_monitoring_pipeline_component.py
git commit -m "feat: wire current auth history into pipeline"
```

---

### Task 4: Add Baseline Snapshot Builder Behind a Feature Flag

**Files:**
- Create: `src/pricing/baseline/build_snapshot.py`
- Create: `scripts/components/build_baseline_snapshot.py`
- Create: `azureml/components/build_baseline_snapshot.yml`
- Test: `tests/test_build_baseline_snapshot.py`

- [ ] **Step 1: Write failing baseline test**

Create `tests/test_build_baseline_snapshot.py`:

```python
from pathlib import Path

from pricing.baseline import build_baseline_snapshot


def test_build_baseline_snapshot_selects_contract_columns(tmp_path):
    feature_table = tmp_path / "feature_table.csv"
    output_path = tmp_path / "model_output_snapshot.csv"
    feature_table.write_text(
        "kpn,vpareadescription,distysegment,Balanced,P20_PRICE,P50_PRICE,P85_PRICE,revenue_sum\n"
        "KPN_1,VP_1,SEG_1,10,8,10,12,100\n",
        encoding="utf-8",
    )

    result = build_baseline_snapshot(feature_table, output_path, run_id="baseline-run")

    text = output_path.read_text(encoding="utf-8")
    assert result.row_count == 1
    assert "baseline-run" in text
    assert "baseline_mlops_pricing_v1" in text
```

- [ ] **Step 2: Implement baseline module**

Create `src/pricing/baseline/build_snapshot.py` with a small CSV transformer that:

```python
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


BASELINE_VERSION = "baseline_mlops_pricing_v1"
OUTPUT_SCHEMA_VERSION = "model_output_snapshot_v1"
REQUIRED_COLUMNS = ("kpn", "vpareadescription", "distysegment", "P20_PRICE", "P50_PRICE", "P85_PRICE")
RECOMMENDATION_COLUMNS = ("Selected_Optimal_Price", "selected_recommended_price", "Balanced", "More_Profit", "Revenue_Aggressive")


@dataclass(frozen=True)
class BaselineSnapshotResult:
    output_path: Path
    row_count: int
    recommendation_column: str


def build_baseline_snapshot(feature_table_path: str | Path, output_path: str | Path, run_id: str) -> BaselineSnapshotResult:
    rows = _read_csv(Path(feature_table_path))
    columns = set(rows[0]) if rows else set()
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise ValueError(f"feature table is missing required baseline columns: {missing}")
    recommendation_column = next((column for column in RECOMMENDATION_COLUMNS if column in columns), "")
    if not recommendation_column:
        raise ValueError(f"feature table is missing recommendation column; tried {RECOMMENDATION_COLUMNS}")

    output_rows = []
    for row in rows:
        output_rows.append(
            {
                **row,
                "run_id": run_id,
                "baseline_version": BASELINE_VERSION,
                "output_schema_version": OUTPUT_SCHEMA_VERSION,
            }
        )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(output, output_rows)
    return BaselineSnapshotResult(output_path=output, row_count=len(output_rows), recommendation_column=recommendation_column)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
```

- [ ] **Step 3: Run baseline tests**

Run:

```bash
cd /Users/me/Developer/tecmx-team46-pricing/pricing-mlops
python -m pytest tests/test_build_baseline_snapshot.py -v
```

Expected: PASS.

- [ ] **Step 4: Add component but do not make it default path yet**

Create `scripts/components/build_baseline_snapshot.py` and `azureml/components/build_baseline_snapshot.yml` following the same wrapper pattern as Task 2. Keep the pipeline default using `baseline_snapshot_blob_path`; add docs saying baseline generation is opt-in until business approval.

- [ ] **Step 5: Commit**

```bash
git add src/pricing/baseline/build_snapshot.py scripts/components/build_baseline_snapshot.py azureml/components/build_baseline_snapshot.yml tests/test_build_baseline_snapshot.py
git commit -m "feat: add opt-in baseline snapshot builder"
```

---

### Task 5: Replace Simulated Handoff With Real Action Contract

**Files:**
- Create: `src/pricing_mlops/operations/handoff.py`
- Modify: `scripts/components/notify_operational_decision.py`
- Test: `tests/test_operational_handoff_contract.py`

- [ ] **Step 1: Write handoff contract test**

Create `tests/test_operational_handoff_contract.py`:

```python
from pricing_mlops.operations.handoff import build_handoff_action


def test_red_decision_holds_scoring():
    action = build_handoff_action({"run_readiness_status": "Red", "recommended_operational_action": "FIX_DATA_QUALITY_BEFORE_DECISION"})
    assert action["action_type"] == "hold"
    assert action["requires_human_review"] is True


def test_green_decision_allows_publish():
    action = build_handoff_action({"run_readiness_status": "Green", "recommended_operational_action": "KEEP_CURRENT_RECOMMENDATIONS"})
    assert action["action_type"] == "publish"
    assert action["requires_human_review"] is False
```

- [ ] **Step 2: Implement deterministic handoff mapping**

Create `src/pricing_mlops/operations/handoff.py`:

```python
from __future__ import annotations


def build_handoff_action(decision: dict[str, object]) -> dict[str, object]:
    status = str(decision.get("run_readiness_status", "Not_Evaluable"))
    recommended_action = str(decision.get("recommended_operational_action", ""))
    if status == "Red":
        return {
            "action_type": "hold",
            "requires_human_review": True,
            "recommended_operational_action": recommended_action,
        }
    if status in {"Yellow", "Watch", "Not_Evaluable"}:
        return {
            "action_type": "review",
            "requires_human_review": True,
            "recommended_operational_action": recommended_action,
        }
    return {
        "action_type": "publish",
        "requires_human_review": False,
        "recommended_operational_action": recommended_action,
    }
```

- [ ] **Step 3: Run tests**

Run:

```bash
cd /Users/me/Developer/tecmx-team46-pricing/pricing-mlops
python -m pytest tests/test_operational_handoff_contract.py -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add src/pricing_mlops/operations/handoff.py tests/test_operational_handoff_contract.py
git commit -m "feat: define operational handoff action contract"
```

---

### Task 6: Update Documentation and Run Full Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/compute-target-contract.md`
- Modify: `docs/platform-contract.md`

- [ ] **Step 1: Update README flow**

Change the flow in `README.md` to:

```text
Azure ML batch endpoint pricing-auth-monitoring/blue
-> pricing_mlops_auth_monitoring_pipeline
-> validate_prepare
-> prepare_current_auth_history
-> build_monitoring_inputs
-> calculate_recommendation_validity
-> calculate_auth_history_drift
-> calculate_operational_decision
-> simulate_operational_handoff
-> publish_outputs
-> notify_operational_decision
-> Storage MLOps outputs versionados
```

Add a "Remaining original-plan gaps" section:

```text
Remaining original-plan gaps:
- full Avance 2 feature engineering from raw/general transaction data;
- baseline snapshot generation as default pipeline branch;
- real scoring/model champion execution;
- full SQL audit tables;
- real external notification or dashboard.
```

- [ ] **Step 2: Update compute contract**

In `docs/compute-target-contract.md`, add:

```markdown
| `pricing_mlops_prepare_current_auth_history` | `scripts/components/prepare_current_auth_history.py` | `current_auth_history_snapshot_real.csv` |
```

and state:

```text
`current_history_blob_path` can point to raw/current masked data. The pipeline now materializes the normalized monitoring snapshot before `build_monitoring_inputs`.
```

- [ ] **Step 3: Run full verification**

Run:

```bash
cd /Users/me/Developer/tecmx-team46-pricing/pricing-mlops
python -m compileall src scripts tests
python -m pytest
```

Expected: both commands exit 0.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/compute-target-contract.md docs/platform-contract.md
git commit -m "docs: document end-to-end auth monitoring pipeline"
```

---

## Rollout Goal

After Tasks 1-3, the operational pipeline closes the biggest current gap:

```text
raw-masked/current input
-> current_auth_history_snapshot_real.csv
-> monitoring
-> published outputs
```

After Task 4, baseline generation exists but remains opt-in until the business agrees how to promote a baseline:

```text
feature table
-> model_output_snapshot.csv
```

After Task 5, the pipeline has a stable action contract that can later drive Teams, Slack, email, dashboard, or scoring automation.

---

## Self-Review

Spec coverage:
- Current history gap is covered by Tasks 1-3.
- Baseline/model output snapshot gap is covered by Task 4.
- Simulated handoff gap is covered by Task 5.
- Documentation and verification are covered by Task 6.
- Full ADF, private networking, and SQL audit are intentionally out of this implementation plan because they involve platform architecture and should be separate plans.

Placeholder scan:
- No implementation task uses "TBD" or undefined code references.
- Later production items are explicitly scoped as separate plans rather than left vague inside this plan.

Type consistency:
- `prepare_current_auth_history(input_path, output_dir, run_id)` is used consistently in tests and script wrapper.
- `build_baseline_snapshot(feature_table_path, output_path, run_id)` is used consistently in tests and implementation.
