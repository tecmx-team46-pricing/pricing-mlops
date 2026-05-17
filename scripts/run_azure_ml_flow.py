#!/usr/bin/env python
from __future__ import annotations

import os
import sys

from scripts.run_azure_storage_flow import main as run_storage_flow


def main() -> int:
    os.environ.setdefault("MLOPS_COMPUTE_TARGET", "azure-ml")
    return run_storage_flow()


if __name__ == "__main__":
    raise SystemExit(main())
