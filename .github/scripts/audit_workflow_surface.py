#!/usr/bin/env python3
"""Static workflow-surface audit for the fixture repository.

Asserts the canonical plural ``lanes`` dispatch selector, full-SHA action pins,
timeout and concurrency coverage (parsed from the real YAML keys, not
substrings), and the exact control-plane scenario enumeration. Callable
reusable workflows keep their singular ``lane`` input; workflow_dispatch
callers derive the selector from ``inputs.lanes``.
Stdlib-only, mirroring the other scripts in this directory.
"""

import json
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
LEGACY_EVIDENCE_MARKERS = (
    "--bin evidence",
    "--field ",
    'payload["fields"]',
    "payload['fields']",
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


def evidence_schema_failures(texts):
    """Require the provenance-bearing v2 evidence surface."""
    failures = []
    for name, text in sorted(texts.items()):
        for marker in LEGACY_EVIDENCE_MARKERS:
            if marker in text:
                failures.append(
                    f"{name}: legacy evidence marker {marker!r}; use the shared v2 verifier"
                )

    rust_text = texts.get("_rust-suite.yml", "")
    if rust_text and "uses: ./.github/actions/collect-evidence" not in rust_text:
        failures.append("_rust-suite.yml: Rust evidence must use the shared collector")
    if rust_text and "uses: ./.github/actions/compare-evidence" not in rust_text:
        failures.append("_rust-suite.yml: Rust evidence must use the shared comparator")
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


def check_callable_lane_block(name, block, failures):
    """Validate one singular callable ``lane`` input block."""
    if scalar_field(block, "type") != "string":
        failures.append(f"{name}: lane input must be type string")
    if scalar_field(block, "required") == "true":
        return

    options = set(block_option_values(block, "options"))
    if not options or not options <= LANE_OPTIONS:
        failures.append(
            f"{name}: lane options must be a non-empty subset of {sorted(LANE_OPTIONS)}, got {sorted(options)}"
        )
    default = scalar_field(block, "default")
    if default != "both":
        failures.append(f"{name}: lane default must be both, got {default!r}")


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


def job_step_blocks(body):
    """Yield actual ``steps`` list items from a job body."""
    lines = list(body)
    steps_index = next(
        (
            index
            for index, line in enumerate(lines)
            if re.match(r"^    steps:\s*(?:#.*)?$", line)
        ),
        None,
    )
    if steps_index is None:
        return []

    steps_indent = indent_of(lines[steps_index])
    step_indent = None
    blocks = []
    current = None
    for line in lines[steps_index + 1 :]:
        stripped = line.strip()
        current_indent = indent_of(line)
        if stripped and current_indent <= steps_indent:
            break
        if not stripped:
            if current is not None:
                current.append(line)
            continue
        if step_indent is None:
            if stripped.startswith("-") and current_indent > steps_indent:
                step_indent = current_indent
            else:
                continue
        if current_indent == step_indent and stripped.startswith("-"):
            if current is not None:
                blocks.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
    if current is not None:
        blocks.append(current)
    return blocks


def step_uses(step, action):
    return any(
        re.match(rf"^\s*(?:-\s*)?uses:\s*{re.escape(action)}@\S+", line)
        for line in step
    )


def step_with_names(step):
    """Extract names from actual ``with.name`` keys in one step."""
    names = []
    for index, line in enumerate(step):
        if not re.match(r"^\s*with:\s*(?:#.*)?$", line):
            continue
        with_indent = indent_of(line)
        for following in step[index + 1 :]:
            stripped = following.strip()
            following_indent = indent_of(following)
            if stripped and following_indent <= with_indent:
                break
            match = re.match(r"^\s+name:\s*(.*)$", following)
            if match:
                names.append(match.group(1).strip().strip("\"'"))
    return names


def build_matrix_arrays(body):
    """Parse JSON arrays embedded in the build job's matrix expression."""
    lines = list(body)
    matrix_index = next(
        (
            index
            for index, line in enumerate(lines)
            if re.match(r"^      matrix:\s*(?:#.*)?$", line)
        ),
        None,
    )
    if matrix_index is None:
        return []

    matrix_indent = indent_of(lines[matrix_index])
    matrix_lines = []
    for line in lines[matrix_index + 1 :]:
        if line.strip() and indent_of(line) <= matrix_indent:
            break
        matrix_lines.append(line)

    arrays = []
    for encoded in re.findall(r"\[\{.*?\}\]", "\n".join(matrix_lines), re.DOTALL):
        try:
            parsed = json.loads(encoded)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
            arrays.append(parsed)
    return arrays


def remote_sha_failures(texts):
    failures = []
    for name, text in texts.items():
        for i, line in enumerate(text.splitlines(), start=1):
            match = re.match(r"^\s*(?:-\s*)?uses:\s*(\S+)", line)
            if not match:
                continue
            ref = match.group(1)
            if ref.startswith("./"):
                continue
            if "@" not in ref or not SHA_RE.search(ref + " "):
                failures.append(
                    f"{name}:{i}: remote action not full-SHA-pinned: {ref}"
                )
    return failures


def pages_policy_failures(texts):
    pages = ""
    if hasattr(texts, "items"):
        for path, text in texts.items():
            normalized_path = str(path).replace("\\", "/")
            if normalized_path.endswith("/.github/workflows/pages.yml") or normalized_path == ".github/workflows/pages.yml" or normalized_path.endswith("/pages.yml") or normalized_path == "pages.yml":
                pages = str(text)
                break
    else:
        for item in texts:
            if isinstance(item, (tuple, list)) and len(item) == 2:
                path, text = item
                normalized_path = str(path).replace("\\", "/")
                if normalized_path.endswith("/.github/workflows/pages.yml") or normalized_path == ".github/workflows/pages.yml" or normalized_path.endswith("/pages.yml") or normalized_path == "pages.yml":
                    pages = str(text)
                    break

    lines = pages.splitlines()
    jobs_start = next((index for index, line in enumerate(lines) if line.strip() == "jobs:"), None)
    jobs = {}
    if jobs_start is not None:
        current_job = None
        for line in lines[jobs_start + 1:]:
            if line and not line[0].isspace():
                break
            if line.startswith("  ") and not line.startswith("    ") and line.strip().endswith(":"):
                current_job = line.strip()[:-1]
                jobs[current_job] = []
            elif current_job is not None:
                jobs[current_job].append(line)

    failures = []
    build = "\n".join(jobs.get("build", []))
    matrix_arrays = build_matrix_arrays(jobs.get("build", []))
    has_velnor_non_writer = any(
        item.get("lane") == "velnor" and item.get("writer") is False
        for array in matrix_arrays
        for item in array
    )
    has_github_writer = any(
        item.get("lane") == "github" and item.get("writer") is True
        for array in matrix_arrays
        for item in array
    )
    has_dual_writer_branch = any(
        any(item.get("lane") == "velnor" and item.get("writer") is False for item in array)
        and any(item.get("lane") == "github" and item.get("writer") is True for item in array)
        for array in matrix_arrays
    )
    if not has_velnor_non_writer or not has_dual_writer_branch:
        failures.append("pages.yml: missing the Velnor non-writer marker in the build matrix")
    if not has_github_writer or not has_dual_writer_branch:
        failures.append("pages.yml: missing the GitHub writer marker in the build matrix")

    if "compare" not in jobs:
        failures.append("pages.yml: missing top-level compare job")
    else:
        download_names = [
            name
            for step in job_step_blocks(jobs["compare"])
            if step_uses(step, "actions/download-artifact")
            for name in step_with_names(step)
        ]
        if sorted(download_names) != ["pages-evidence-github", "pages-evidence-velnor"]:
            failures.append("pages.yml: compare must contain both evidence artifact names")

        compare = "\n".join(jobs["compare"])
        condition = "".join(compare.split())
        has_push = "'push'" in condition or '"push"' in condition
        has_dispatch = "workflow_dispatch" in condition
        has_both = "inputs.lanes=='both'" in condition or 'inputs.lanes=="both"' in condition
        if not (has_push and has_dispatch and has_both):
            failures.append("pages.yml: compare condition must allow push and both-lane dispatch")

    deploy = "\n".join(jobs.get("deploy", []))
    if not any(line.strip().replace(" ", "").replace("\t", "") == "needs:[build,compare]" for line in deploy.splitlines()):
        failures.append("pages.yml: deploy must declare needs: [build, compare]")
    deploy_condition = "".join(deploy.split())
    if not ("needs.compare.result=='success'" in deploy_condition or 'needs.compare.result=="success"' in deploy_condition):
        failures.append("pages.yml: deploy condition must require compare success")
    allowed_deploy_paths = (
        "github.event_name=='push'" in deploy_condition
        and "github.event_name=='workflow_dispatch'&&inputs.lanes=='github'"
        in deploy_condition
        and "github.event_name=='workflow_dispatch'&&inputs.lanes=='both'"
        in deploy_condition
    )
    if not allowed_deploy_paths:
        failures.append(
            "pages.yml: deploy must allow only push, GitHub dispatch, or both-lane dispatch"
        )

    has_evidence_upload = any(
        step_uses(step, "actions/upload-artifact")
        and any(name.startswith("pages-evidence-") for name in step_with_names(step))
        for step in job_step_blocks(jobs.get("build", []))
    )
    if not has_evidence_upload:
        failures.append("pages.yml: build must contain a pages-evidence upload-artifact step")

    return failures


def audit():
    failures = []
    texts = workflow_texts()
    failures.extend(automatic_l2_failures(texts))

    # Rust fixture workloads use nextest. Restrict this check to the named
    # harness package so legitimate ordinary `cargo test` commands remain
    # available for unrelated diagnostic or negative fixtures.
    failures.extend(cargo_policy_failures(texts))

    # Evidence must be collected and compared through the provenance-bearing
    # v2 verifier. Authored v1 fields are claims, not observations.
    failures.extend(evidence_schema_failures(texts))

    # 1. Full-SHA pins for every remote `uses:` in every workflow.
    failures.extend(remote_sha_failures(texts))

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

    # 3. Sole `lane` selector wherever it is declared. Required callable
    # wrappers name their lane explicitly; optional callable inputs retain the
    # dual-lane options/default contract.
    for name, text in texts.items():
        block = input_block(text, "lane")
        if block is None:
            continue
        check_callable_lane_block(name, block, failures)

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

    failures.extend(pages_policy_failures(texts))
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
