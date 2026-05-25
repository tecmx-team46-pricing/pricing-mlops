# Artifact Publishing Contract

## Ownership

`pricing_mlops.run` owns ML execution and produces a neutral `RunResult`.
Publishing is owned by `pricing_mlops.artifact_publishing`.

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

`ComponentStateLayout` owns the intermediate Azure ML component-state prefixes used by `validate_prepare`, `score_evaluate`, and `publish_outputs`:

```text
artifacts/component-state/<run_id>/prepared/
artifacts/component-state/<run_id>/run_artifacts/
```

Those intermediate files are not the final publication contract; they exist only to make multi-component AML execution restartable and idempotent.

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

## Declarative Configuration

Publication can be selected by environment variables without changing ML code:

| Variable | Default | Purpose |
|---|---|---|
| `MLOPS_ARTIFACT_SINKS` | `azure_blob` | Comma-separated enabled sinks. Supported names are `azure_blob`, `azure_ml`, `sql_metadata`, and `local` where the caller wires the dependency. |
| `MLOPS_OPTIONAL_ARTIFACT_SINKS` | `azure_ml,sql_metadata` | Comma-separated sinks that should not fail required artifact publication. |
| `MLOPS_CONTAINER_CURATED` | `curated` | Curated output container. |
| `MLOPS_CONTAINER_RUNS` | `runs` | Run metadata container. |
| `MLOPS_CONTAINER_SNAPSHOTS` | `snapshots` | Snapshot container. |
| `MLOPS_CONTAINER_DRIFT_LOGS` | `drift-logs` | Drift log container. |
| `MLOPS_CONTAINER_REPORTS` | `reports` | Report container. |
| `MLOPS_CONTAINER_ARTIFACTS` | `artifacts` | General artifacts container. |

The current production path enables `azure_blob` only. Azure ML and SQL sinks are implemented as optional fan-out destinations and must be explicitly wired by the caller with the appropriate client/connection.

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

`RetryPolicy` wraps transient sink operations for Azure Blob, Azure ML tracking, and SQL metadata upsert. The default policy retries common Azure SDK transport/timeout error classes and does not retry definitive validation or contract errors.

Each retry opens the source file again before uploading, so a partially consumed stream is not reused after a transient upload failure.

## Observability And Security

Each sink returns a `SinkPublishResult` containing sink name, status, published targets, failed targets, and optional manifest URI. Callers should log this object as structured metadata.

No sink accepts account keys or connection strings as part of the neutral domain contract. Azure clients and SQL connections are injected by the caller, which keeps credential acquisition in infrastructure code.

## Compatibility

Existing scripts keep their public CLI contracts:

- `scripts/upload_run_outputs.py`
- `scripts/run_azure_storage_flow.py`
- `scripts/components/publish_outputs.py`

They now route through `ArtifactLayout` and `AzureBlobArtifactSink` while preserving current file names, containers, and blob prefixes.
