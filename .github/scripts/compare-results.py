#!/usr/bin/env python3
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
packages = ["app-a", "app-b"]

def load(path: Path) -> dict:
    with path.open() as handle:
        return json.load(handle)

compared = 0
skipped = []
for package in packages:
    github_path = root / f"result-github-{package}" / "result.json"
    velnor_path = root / f"result-velnor-{package}" / "result.json"
    if not github_path.exists() or not velnor_path.exists():
        missing = [l for l, p in [("github", github_path), ("velnor", velnor_path)] if not p.exists()]
        skipped.append(f"{package} (missing: {', '.join(missing)})")
        continue
    github = load(github_path)
    velnor = load(velnor_path)
    github.pop("lane", None)
    velnor.pop("lane", None)
    if github != velnor:
        raise SystemExit(f"mismatch for {package}: github={github} velnor={velnor}")
    compared += 1

if skipped:
    print(f"skipped (single-lane run): {', '.join(skipped)}")
if compared > 0:
    print(f"fixture results match ({compared} package(s) compared)")
elif not skipped:
    raise SystemExit("no results to compare")
