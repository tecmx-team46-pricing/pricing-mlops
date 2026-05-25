from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 3
    delay_seconds: float = 0.25
    transient_error_names: tuple[str, ...] = (
        "ServiceRequestError",
        "ServiceResponseError",
        "ResourceModifiedError",
        "TimeoutError",
    )

    def run(self, operation: Callable[[], T]) -> T:
        last_error: Exception | None = None
        for attempt in range(1, self.attempts + 1):
            try:
                return operation()
            except Exception as exc:
                last_error = exc
                if attempt == self.attempts or not self.is_transient(exc):
                    raise
                time.sleep(self.delay_seconds)
        raise RuntimeError("retry policy exhausted") from last_error

    def is_transient(self, exc: Exception) -> bool:
        return exc.__class__.__name__ in self.transient_error_names
