from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from pricing_mlops.artifacts.models import RunResult


class PublishStatus(str, Enum):
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class SinkPublishResult:
    sink_name: str
    status: PublishStatus
    published: dict[str, str] = field(default_factory=dict)
    failed: dict[str, str] = field(default_factory=dict)
    manifest_uri: str | None = None

    @property
    def ok(self) -> bool:
        return self.status in {PublishStatus.SUCCEEDED, PublishStatus.SKIPPED}


@dataclass(frozen=True)
class PublishResult:
    status: PublishStatus
    sinks: tuple[SinkPublishResult, ...]

    @property
    def ok(self) -> bool:
        return self.status == PublishStatus.SUCCEEDED


class ArtifactSink(Protocol):
    name: str
    required: bool

    def publish(self, run_result: RunResult) -> SinkPublishResult:
        ...


class ArtifactPublisher:
    def __init__(self, sinks: tuple[ArtifactSink, ...]):
        self._sinks = sinks

    def publish(self, run_result: RunResult) -> PublishResult:
        results = tuple(self._publish_to_sink(sink, run_result) for sink in self._sinks)
        required_failures = [
            result
            for sink, result in zip(self._sinks, results, strict=True)
            if sink.required and not result.ok
        ]
        any_failures = [result for result in results if not result.ok]
        if required_failures:
            status = PublishStatus.FAILED
        elif any_failures:
            status = PublishStatus.PARTIAL
        else:
            status = PublishStatus.SUCCEEDED
        return PublishResult(status=status, sinks=results)

    @staticmethod
    def _publish_to_sink(sink: ArtifactSink, run_result: RunResult) -> SinkPublishResult:
        try:
            return sink.publish(run_result)
        except Exception as exc:
            return SinkPublishResult(
                sink_name=sink.name,
                status=PublishStatus.FAILED,
                failed={"sink": str(exc)},
            )
