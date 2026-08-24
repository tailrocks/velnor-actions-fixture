#!/usr/bin/env python3
"""Static workflow-surface audit for the fixture repository.

Asserts the canonical plural ``lanes`` dispatch selector, full-SHA action pins,
timeout and concurrency coverage, and the exact control-plane scenario
enumeration. Callable reusable workflows keep their singular ``lane`` input;
workflow_dispatch callers derive the selector from ``inputs.lanes``.
Stdlib-only, mirroring the other scripts in this directory.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"

# ci.yml is rendered by velnor-actions-generator ("DO NOT EDIT") and still
# carries the superseded sole-lane dispatch input pinned to mirrored release
# 2026.8.30. The generator's plural-`lanes` render has not been propagated to
# that file yet; until it is re-rendered upstream, ci.yml is the only permitted
# dispatch-level sole-`lane` exception. Never hand-edit ci.yml here.
GENERATOR_PENDING_SOLE_LANE = frozenset({"ci.yml"})

CONTROL_PLANE_SCENARIOS = {
    "success",
    "failure",
    "hold",
    "queue",
    "concurrent",
    "artifacts",
    "cache",
    "load",
}

LANE_OPTIONS = {"velnor", "github", "both"}
SHA_RE = re.compile(r"@[0-9a-f]{40}(\s|$|#)")


def workflow_texts():
    return {p.name: p.read_text() for p in sorted(WORKFLOWS.glob("*.yml"))}


def indent_of(line):
    return len(line) - len(line.lstrip())


def dispatch_inputs(text):
    """Map each ``on.workflow_dispatch.inputs`` name to its body lines."""
    lines = text.splitlines()
    try:
        start = next(
            i for i, line in enumerate(lines) if line.rstrip() == "  workflow_dispatch:"
        )
    except StopIteration:
        return {}
    inputs = {}
    in_inputs = False
    current_name = None
    current_body = []
    for line in lines[start + 1 :]:
        if line.strip() and indent_of(line) <= 1:
            break
        if not line.strip():
            continue
        stripped = line.strip()
        if indent_of(line) == 4 and stripped == "inputs:":
            in_inputs = True
            continue
        if not in_inputs:
            continue
        if indent_of(line) == 6 and stripped.endswith(":") and ":" not in stripped[:-1]:
            if current_name is not None:
                inputs[current_name] = current_body
            current_name = stripped[:-1]
            current_body = []
        elif current_name is not None:
            current_body.append(line)
    if current_name is not None:
        inputs[current_name] = current_body
    return inputs


def input_block(text, name):
    """Return the lines of an ``on.<dispatch>.inputs.<name>`` block, if any."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(rf"^(\s+){re.escape(name)}:\s*$", line):
            indent = len(line) - len(line.lstrip())
            block = []
            for later in lines[i + 1 :]:
                later_indent = len(later) - len(later.lstrip())
                if not later.strip() or later_indent <= indent:
                    break
                block.append(later)
            return block
    return None


def block_option_values(block, field):
    """Extract option values from a nested ``field:`` block or flow list."""
    values = []
    collecting = False
    field_indent = 0
    for line in block:
        stripped = line.strip()
        current_indent = len(line) - len(line.lstrip())
        if stripped.startswith(f"{field}:"):
            rest = stripped[len(field) + 1 :].strip()
            if rest.startswith("[") and rest.endswith("]"):
                inner = rest[1:-1].strip()
                if inner:
                    values = [item.strip() for item in inner.split(",")]
                return values
            collecting = True
            field_indent = current_indent
            continue
        if collecting and current_indent > field_indent and stripped.startswith("- "):
            values.append(stripped[2:].strip())
            continue
        if collecting and stripped and current_indent <= field_indent:
            break
    return values


def scalar_field(block, field):
    for line in block:
        stripped = line.strip()
        if stripped.startswith(f"{field}:"):
            return stripped[len(field) + 1 :].strip().strip("'\"")
    return None


def top_level_jobs(text):
    """Yield (job_id, job_body_lines) for each entry of the jobs: mapping."""
    lines = text.splitlines()
    try:
        jobs_index = next(i for i, l in enumerate(lines) if l.rstrip() == "jobs:")
    except StopIteration:
        return
    for i, line in enumerate(lines[jobs_index + 1 :], start=jobs_index + 1):
        match = re.match(r"^  ([A-Za-z0-9_-]+):\s*(#.*)?$", line)
        if match and not line.startswith("   "):
            body = []
            for later in lines[i + 1 :]:
                if re.match(r"^  [A-Za-z0-9_-]+:\s*$", later):
                    break
                body.append(later)
            yield match.group(1), body


def check_lanes_block(name, block, failures):
    """Validate one plural ``lanes`` dispatch input block."""
    if scalar_field(block, "type") != "choice":
        failures.append(f"{name}: lanes input must be type choice")
    options = set(block_option_values(block, "options"))
    if options != LANE_OPTIONS:
        failures.append(
            f"{name}: lanes options must be exactly {sorted(LANE_OPTIONS)}, got {sorted(options)}"
        )
    default = scalar_field(block, "default")
    if default != "velnor":
        failures.append(f"{name}: lanes default must be velnor, got {default!r}")


def audit():
    failures = []
    texts = workflow_texts()

    # 1. Full-SHA pins for every remote `uses:` in every workflow.
    for name, text in texts.items():
        for i, line in enumerate(text.splitlines(), start=1):
            match = re.match(r"^\s*uses:\s*(\S+)", line)
            if not match:
                continue
            ref = match.group(1)
            if ref.startswith("./"):
                continue
            if "@" not in ref or not SHA_RE.search(ref + " "):
                failures.append(
                    f"{name}:{i}: remote action not full-SHA-pinned: {ref}"
                )

    # 2. Dispatch callers use exactly the canonical plural `lanes` selector.
    # Callable reusable workflows keep their singular `lane` input; callers
    # derive it from `inputs.lanes`. ci.yml stays exempt only until the
    # generator propagates its plural-`lanes` render (see
    # GENERATOR_PENDING_SOLE_LANE).
    for name, text in texts.items():
        inputs = dispatch_inputs(text)
        if not inputs:
            continue
        if "lane" in inputs:
            is_reusable = re.search(r"^  workflow_call:", text, re.MULTILINE)
            if not is_reusable and name not in GENERATOR_PENDING_SOLE_LANE:
                failures.append(
                    f"{name}: dispatch selector must be plural `lanes`, found sole `lane`"
                )
        if "lanes" in inputs:
            check_lanes_block(name, inputs["lanes"], failures)

    # 3. Sole `lane` selector wherever it is declared (reusables and any
    # pending generator output). Negative fixtures may intentionally restrict
    # to a subset of lanes (no `both`, since a negative proof runs on one
    # lane); they must still stay within the canonical set.
    for name, text in texts.items():
        block = input_block(text, "lane")
        if block is None:
            continue
        options = set(block_option_values(block, "options"))
        if not options or not options <= LANE_OPTIONS:
            failures.append(
                f"{name}: lane options must be a non-empty subset of {sorted(LANE_OPTIONS)}, got {sorted(options)}"
            )
        default = scalar_field(block, "default")
        if default != "velnor":
            failures.append(f"{name}: lane default must be velnor, got {default!r}")

    # 4. compat.yml and control-plane.yml are workflow_dispatch callers and
    # must declare the full canonical plural `lanes` selector.
    for name in ("compat.yml", "control-plane.yml"):
        inputs = dispatch_inputs(texts[name])
        if "lanes" not in inputs:
            failures.append(f"{name}: missing plural `lanes` dispatch input")
            continue
        check_lanes_block(name, inputs["lanes"], failures)

    # 5. control-plane enumerates exactly the eight scenarios.
    cp_text = texts["control-plane.yml"]
    scenario_block = input_block(cp_text, "scenario")
    scenarios = set(block_option_values(scenario_block, "options"))
    if scenarios != CONTROL_PLANE_SCENARIOS:
        failures.append(
            "control-plane.yml: scenario options must be exactly "
            f"{sorted(CONTROL_PLANE_SCENARIOS)}, got {sorted(scenarios)}"
        )

    # 6. Every control-plane job carries timeout-minutes and its own concurrency.
    for job_id, body in top_level_jobs(cp_text):
        joined = "\n".join(body)
        if "timeout-minutes:" not in joined:
            failures.append(f"control-plane.yml: job {job_id} missing timeout-minutes")
        if "concurrency:" not in joined or "group:" not in joined:
            failures.append(f"control-plane.yml: job {job_id} missing concurrency group")

    # 7. Every compat.yml job keeps its measured timeout; the workflow keeps
    # its intentional concurrency group.
    compat_text = texts["compat.yml"]
    if not re.search(r"^concurrency:", compat_text, re.MULTILINE):
        failures.append("compat.yml: missing workflow-level concurrency group")
    for job_id, body in top_level_jobs(compat_text):
        if "timeout-minutes:" not in "\n".join(body):
            failures.append(f"compat.yml: job {job_id} missing timeout-minutes")

    return failures


def main():
    failures = audit()
    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"workflow-surface audit: {len(failures)} failure(s)")
        return 1
    print("workflow-surface audit: ok (plural lanes selector, SHA pins, timeouts, concurrency, eight scenarios)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
