#!/usr/bin/env python
from __future__ import annotations

import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scripts.run_azure_storage_flow import main as run_storage_flow


def main() -> int:
    os.environ.setdefault("MLOPS_COMPUTE_TARGET", "azure-ml")
    return run_storage_flow()


if __name__ == "__main__":
    raise SystemExit(main())
