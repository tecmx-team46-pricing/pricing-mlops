# Artifact Publishing Contract

## Ownership

`pricing_mlops.run` owns ML execution and produces a neutral `RunResult`.
Publishing is owned by `pricing_mlops.artifacts`.

Domain code must not import Azure, SQL, cloud SDKs, account keys, connection strings, or platform paths. Infrastructure integrations live behind artifact sinks.

## Neutral Model

The neutral contract is:

| Type | Purpose |
|---|---|
| `RunMetadata` | Run identity, status, row counts, drift status, versions, input reference, and optional model source metadata. |
| `RunArtifact` | One local artifact reference with logical name, filename, path, content type, and required flag. |
| `ArtifactManifest` | Versioned collection of artifacts for a run. |
| `RunResult` | Metadata plus manifest, independent from publication destination. |

The current required artifact filenames remain:

```text
curated_pricing.csv
model_output_snapshot.csv
model_drift_log.json
model_run_log.json
report.md
```

## Layout

`ArtifactLayout` and `RunPartition` own path construction. The current Azure Blob layout remains:

```text
<container>/environment=<env>/compute=<compute>/trigger=<trigger>/owner=<owner>/run_date=<yyyymmdd>/run_id=<run_id>/<artifact>
```

The same `curated_pricing.csv` is published to both `curated` and `artifacts` for compatibility with the existing platform contract.

## Publishing

`ArtifactSink` is the sink interface. `ArtifactPublisher` fans out one `RunResult` to one or more sinks and returns a `PublishResult`.

Sink results are explicit:

| Status | Meaning |
|---|---|
| `succeeded` | Sink published its contract. |
| `partial` | Some artifacts published and some failed. |
| `failed` | Required publication failed. |
| `skipped` | Sink intentionally did nothing. |

Required sinks can fail the overall publish. Optional sinks produce `partial` so operators can see the failure without hiding successful required publication.

## Implemented Sinks

| Sink | Scope |
|---|---|
| `LocalArtifactSink` | Development and tests; copies artifacts to a local run folder and overwrites idempotently. |
| `AzureBlobArtifactSink` | Functional output publication to Storage Blob using identity-based SDK clients and overwrite semantics. |
| `AzureMlArtifactSink` | First scoped AML integration: records tags, row-count metric, and artifact references only. It does not store business artifacts in AML. |
| `SqlRunMetadataSink` | Metadata upsert for queryable run history. It stores run metadata and manifest reference, not large files. |

## Idempotency And Partial Failure

Blob and local sinks overwrite the same `run_id` paths. SQL uses upsert keyed by `run_id`.

Each sink reports published and failed artifact keys. Callers must inspect `PublishResult.status` instead of assuming all-or-nothing success.

## Retry

`RetryPolicy` wraps transient sink operations. The default policy retries common Azure SDK transport/timeout error classes and does not retry definitive validation or contract errors.

## Compatibility

Existing scripts keep their public CLI contracts:

- `scripts/upload_run_outputs.py`
- `scripts/run_azure_storage_flow.py`
- `scripts/components/publish_outputs.py`

They now route through `ArtifactLayout` and `AzureBlobArtifactSink` while preserving current file names, containers, and blob prefixes.
