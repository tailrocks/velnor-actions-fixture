#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

if len(sys.argv) != 4:
    raise SystemExit("usage: write-result.py PACKAGE LANE OUTPUT")
package, lane, output_name = sys.argv[1:]
if lane not in {"github", "velnor"}:
    raise SystemExit(f"unsupported lane: {lane}")
output = Path(output_name)

result = {
    "package": package,
    "lane": lane,
    "label": f"fixture::{package}",
    "evidence": {
        "action": "check-fixture-output",
        "command_file_contract": ["GITHUB_ENV", "GITHUB_OUTPUT", "GITHUB_PATH", "GITHUB_STEP_SUMMARY"],
        "tool": os.environ.get("FIXTURE_TOOL_RESULT", "fixture-tool-ok"),
    },
    "runtime": {"os": "linux", "shell": "bash"},
}

output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
