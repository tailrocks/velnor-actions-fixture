#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

package = sys.argv[1]
lane = sys.argv[2]
output = Path(sys.argv[3])

result = {
    "package": package,
    "lane": lane,
    "label": f"fixture::{package}",
    "env": os.environ["FIXTURE_PACKAGE"],
    "tool": "fixture-tool-ok",
}

output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

