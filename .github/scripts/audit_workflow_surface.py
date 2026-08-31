#!/usr/bin/env python3
"""Static workflow-surface audit for the fixture repository.

Asserts the canonical plural ``lanes`` dispatch selector, full-SHA action pins,
timeout and concurrency coverage (parsed from the real YAML keys, not
substrings), and the exact control-plane scenario enumeration. Callable
reusable workflows keep their singular ``lane`` input; workflow_dispatch
callers derive the selector from ``inputs.lanes``.
Stdlib-only, mirroring the other scripts in this directory.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"

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
AUTOMATIC_L2_CALLS = {
    "l2-runtime.yml": "l2-runtime",
    "l2-provenance.yml": "l2-provenance",
}
SHA_RE = re.compile(r"@[0-9a-f]{40}(\s|$|#)")
FIXTURE_HARNESS_TEST_RE = re.compile(
    r"(?:^|(?:&&|[;&|])\s*|\bthen\s+)cargo\s+test\b[^\n]*"
    r"(?:--package|-p)\s+['\"]?fixture-harness['\"]?(?:\s|$)"
)


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


def run_script_lines(text):
    """Yield (line number, shell line) for workflow ``run`` values."""
    lines = text.splitlines()
    in_run = False
    run_indent = 0
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        indent = indent_of(line)
        if in_run:
            if stripped and indent <= run_indent:
                in_run = False
            else:
                if stripped and not stripped.startswith("#"):
                    yield number, line
                continue
        match = re.match(r"^(\s*)(?:-\s*)?run:\s*(.*)$", line)
        if not match:
            continue
        run_indent = len(match.group(1))
        inline = match.group(2).strip()
        if inline and inline not in {"|", ">", "|-", ">-", "|+", ">+"}:
            if not inline.startswith("#"):
                yield number, inline
        else:
            in_run = True


def cargo_policy_failures(texts):
    """Reject fixture-harness ``cargo test`` while allowing ordinary tests."""
    failures = []
    for name, text in sorted(texts.items()):
        for number, line in run_script_lines(text):
            if FIXTURE_HARNESS_TEST_RE.search(line.strip()):
                failures.append(
                    f"{name}:{number}: fixture-harness commands must use `cargo nextest run`, "
                    "not `cargo test`"
                )
    return failures


def automatic_l2_failures(texts):
    """Require CI to call both L2 diagnostics with their dual-lane default."""
    failures = []
    ci_text = texts.get("ci.yml", "")
    for workflow, job in sorted(AUTOMATIC_L2_CALLS.items()):
        workflow_text = texts.get(workflow, "")
        if not re.search(r"^  workflow_call:\s*$", workflow_text, re.MULTILINE):
            failures.append(f"{workflow}: missing workflow_call trigger")
        if not re.search(
            r"^\s+lane:\s+\{[^}]*default:\s*both\b", workflow_text, re.MULTILINE
        ):
            failures.append(f"{workflow}: workflow_call lane default must be both")
        job_match = re.search(
            rf"^  {re.escape(job)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:|\Z)",
            ci_text,
            re.MULTILINE | re.DOTALL,
        )
        if not job_match:
            failures.append(f"ci.yml: missing automatic L2 job {job}")
            continue
        body = job_match.group(1)
        if f"uses: ./.github/workflows/{workflow}" not in body:
            failures.append(f"ci.yml: {job} must call ./.github/workflows/{workflow}")
        if not re.search(r"^\s+lane:\s+.*(?:both|inputs\.lanes)", body, re.MULTILINE):
            failures.append(f"ci.yml: {job} must pass the automatic both-lane selector")
    return failures


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
    if default != "both":
        failures.append(f"{name}: lanes default must be both, got {default!r}")


def job_declares_timeout(body):
    """True when the job body declares a real ``timeout-minutes`` mapping key.

    Job properties sit exactly one level under the two-space job id, so the
    key is matched at indent 4; comments and step-shell text cannot match.
    """
    return any(re.match(r"^    timeout-minutes:\s*\S", line) for line in body)


def job_declares_concurrency_group(body):
    """True when the job body declares a concurrency mapping with a group key.

    Parses the real YAML keys at the job-property indent (block or flow
    style) instead of substring matching, so comments and unrelated text
    cannot satisfy the audit.
    """
    lines = list(body)
    for i, line in enumerate(lines):
        if re.match(r"^    concurrency:(\s*(?:#.*)?)$", line):
            for later in lines[i + 1 :]:
                stripped = later.strip()
                if not stripped:
                    continue
                if len(later) - len(later.lstrip()) <= 4:
                    break
                if re.match(r"^      group:\s*\S", later):
                    return True
        elif re.match(r"^    concurrency:\s+(\{.*\})\s*(?:#.*)?$", line):
            if re.search(r"\bgroup\s*:", line):
                return True
    return False


def audit():
    failures = []
    texts = workflow_texts()
    failures.extend(automatic_l2_failures(texts))

    # Rust fixture workloads use nextest. Restrict this check to the named
    # harness package so legitimate ordinary `cargo test` commands remain
    # available for unrelated diagnostic or negative fixtures.
    failures.extend(cargo_policy_failures(texts))

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
    # derive it from `inputs.lanes`.
    for name, text in texts.items():
        inputs = dispatch_inputs(text)
        if not inputs:
            continue
        if "lane" in inputs:
            is_reusable = re.search(r"^  workflow_call:", text, re.MULTILINE)
            if not is_reusable:
                failures.append(
                    f"{name}: dispatch selector must be plural `lanes`, found sole `lane`"
                )
        if "lanes" in inputs:
            check_lanes_block(name, inputs["lanes"], failures)

    # 3. Sole `lane` selector wherever it is declared (reusables and any
    # callable reusable workflows use the singular `lane` input; it still
    # defaults to both so callers cannot silently become single-lane.
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
        if default != "both":
            failures.append(f"{name}: lane default must be both, got {default!r}")

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

    # 6. Every control-plane job carries timeout-minutes and its own
    # concurrency group, parsed from the real YAML keys.
    for job_id, body in top_level_jobs(cp_text):
        if not job_declares_timeout(body):
            failures.append(f"control-plane.yml: job {job_id} missing timeout-minutes")
        if not job_declares_concurrency_group(body):
            failures.append(f"control-plane.yml: job {job_id} missing concurrency group")

    # 7. Every compat.yml job keeps its measured timeout; the workflow keeps
    # its intentional concurrency group. Job timeouts are parsed from the
    # real YAML keys.
    compat_text = texts["compat.yml"]
    if not re.search(r"^concurrency:", compat_text, re.MULTILINE):
        failures.append("compat.yml: missing workflow-level concurrency group")
    for job_id, body in top_level_jobs(compat_text):
        if not job_declares_timeout(body):
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
