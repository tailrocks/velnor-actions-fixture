#!/usr/bin/env python3
"""Compare the deterministic semantic payload from both runner lanes."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PACKAGES = ("app-a", "app-b")
LANES = ("github", "velnor")
# These are the only runner-identity fields that may differ. All workload
# fields remain part of the semantic comparison.
IDENTITY_FIELDS = frozenset({"lane", "runner", "runner_name"})


def usage() -> str:
    return "usage: compare-results.py RESULTS_DIRECTORY"


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"invalid result {path}: {error}") from error
    if not isinstance(value, dict):
        raise SystemExit(f"invalid result {path}: root must be an object")
    return value


def result_paths(root: Path) -> dict[tuple[str, str], Path]:
    """Index result evidence and reject duplicate/unexpected lane files."""
    expected = {(lane, package) for package in PACKAGES for lane in LANES}
    indexed: dict[tuple[str, str], Path] = {}
    for path in sorted(root.rglob("result.json")):
        parent = path.parent.name
        prefix = "result-"
        if not parent.startswith(prefix):
            raise SystemExit(f"unexpected result evidence path: {path.relative_to(root)}")
        parts = parent.removeprefix(prefix).split("-", 1)
        if len(parts) != 2 or parts[0] not in LANES:
            raise SystemExit(f"unexpected result evidence directory: {parent}")
        key = (parts[0], parts[1])
        if key not in expected:
            raise SystemExit(f"unexpected result evidence identity: {parent}")
        if key in indexed:
            raise SystemExit(
                f"duplicate lane evidence for {key[1]} ({key[0]}): "
                f"{indexed[key].relative_to(root)} and {path.relative_to(root)}"
            )
        indexed[key] = path

    for lane, package in sorted(expected):
        evidence_dir = root / f"result-{lane}-{package}"
        if not evidence_dir.is_dir():
            raise SystemExit(f"missing required lane evidence directory: {evidence_dir.name}")
        json_files = sorted(evidence_dir.glob("*.json"))
        if json_files != [evidence_dir / "result.json"]:
            names = ", ".join(path.name for path in json_files) or "none"
            raise SystemExit(
                f"missing/duplicate lane evidence for {package} ({lane}): {names}"
            )
        if (lane, package) not in indexed:
            raise SystemExit(f"missing required lane result for {package}: {lane}")
    return indexed


def semantic(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: semantic(item)
            for key, item in sorted(value.items())
            if key not in IDENTITY_FIELDS
        }
    if isinstance(value, list):
        return [semantic(item) for item in value]
    return value


def differing_paths(left: Any, right: Any, path: str = "$") -> list[str]:
    if type(left) is not type(right):
        return [path]
    if isinstance(left, dict):
        result: list[str] = []
        for key in sorted(set(left) | set(right)):
            if key not in left or key not in right:
                result.append(f"{path}.{key}")
            else:
                result.extend(differing_paths(left[key], right[key], f"{path}.{key}"))
        return result
    if isinstance(left, list):
        if len(left) != len(right):
            return [path]
        result = []
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            result.extend(differing_paths(left_item, right_item, f"{path}[{index}]"))
        return result
    return [] if left == right else [path]


def main() -> int:
    if len(sys.argv) != 2:
        print(usage(), file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    if not root.is_dir():
        print(f"results directory does not exist: {root}", file=sys.stderr)
        return 2
    paths = result_paths(root)
    compared = 0
    for package in PACKAGES:
        github_path = paths[("github", package)]
        velnor_path = paths[("velnor", package)]
        github = load(github_path)
        velnor = load(velnor_path)
        for lane, path, result in (
            ("github", github_path, github),
            ("velnor", velnor_path, velnor),
        ):
            if result.get("package") != package:
                raise SystemExit(
                    f"wrong package in {path.relative_to(root)}: "
                    f"expected {package!r}, got {result.get('package')!r}"
                )
            if result.get("lane") != lane:
                raise SystemExit(
                    f"wrong lane in {path.relative_to(root)}: "
                    f"expected {lane!r}, got {result.get('lane')!r}"
                )
        left = semantic(github)
        right = semantic(velnor)
        if left != right:
            paths_text = ", ".join(differing_paths(left, right)[:8])
            raise SystemExit(f"semantic mismatch for {package}: {paths_text}")
        compared += 1
    print(f"fixture results match ({compared} package(s) compared)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
