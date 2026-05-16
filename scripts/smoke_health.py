#!/usr/bin/env python
from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import urlopen


def main() -> int:
    endpoint = os.getenv("FUNCTION_HEALTH_ENDPOINT")
    if not endpoint:
        print(
            "FUNCTION_HEALTH_ENDPOINT is required for smoke_health.py. "
            "Set it to the target environment Function host or full health URL.",
            file=sys.stderr,
        )
        return 4

    url = _health_url(endpoint)
    try:
        with urlopen(url, timeout=15) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        print(f"health check failed: HTTP {exc.code} calling {url}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"health check failed: {exc.reason} calling {url}", file=sys.stderr)
        return 1

    print(f"health check succeeded: {url}")
    if body:
        try:
            print(json.dumps(json.loads(body), indent=2, sort_keys=True))
        except json.JSONDecodeError:
            print(body)
    return 0


def _health_url(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if parsed.path in ("", "/"):
        return urlunparse(parsed._replace(path="/api/health"))
    return endpoint


if __name__ == "__main__":
    raise SystemExit(main())
