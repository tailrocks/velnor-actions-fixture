#!/usr/bin/env python3
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
packages = ["app-a", "app-b"]

def load(path: Path) -> dict:
    with path.open() as handle:
        return json.load(handle)

for package in packages:
    github = load(root / f"result-github-{package}" / "result.json")
    velnor = load(root / f"result-velnor-{package}" / "result.json")
    github.pop("lane", None)
    velnor.pop("lane", None)
    if github != velnor:
        raise SystemExit(f"mismatch for {package}: github={github} velnor={velnor}")

print("fixture results match")

