from __future__ import annotations

from pathlib import Path
import shutil


def copy_tree(source: str | Path, destination: str | Path) -> None:
    source = Path(source)
    destination = Path(destination)
    if source.resolve() == destination.resolve():
        return
    destination.mkdir(parents=True, exist_ok=True)
    for path in source.rglob("*"):
        if path.is_file():
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
