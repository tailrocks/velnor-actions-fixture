#!/usr/bin/env python3
"""Audit Velnor capability coverage and executable workflow policy.

Stdlib-only by design. ``--contract-only`` validates the two JSON contracts
without requiring the repository's staged workflow migration to be complete.
The default mode is the readiness gate and audits current workflow content.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CAPABILITIES_PATH = ROOT / "coverage" / "velnor-capabilities.json"
COVERAGE_PATH = ROOT / "coverage" / "fixture-coverage.json"
SURFACE_COVERAGE_PATH = ROOT / "coverage" / "action-surface-coverage.json"
WORKFLOWS = ROOT / ".github" / "workflows"
ACTIONS = ROOT / ".github" / "actions"

EXPECTED_MANIFEST_VERSION = 10
EXPECTED_SOURCE_SHA = "9578bb09b72e1d5ba638bf33415d34218f89f933"
EXPECTED_ACTION_COUNT = 30
EXPECTED_REUSABLE_WORKFLOW_COUNT = 2
EXPECTED_KACHE_REF = "49398d37113c616fdb61be434cb497e3c2c8f3e6"
EXPECTED_KACHE_VERSION = "v0.14.2"

MICROVM_SUPPORTED = {
    "actions/cache",
    "actions/checkout",
    "mozilla-actions/sccache-action",
    "swatinem/rust-cache",
}
EXPECTED_RUNTIME_SEMANTICS = {
    "command-files-env-path-output-summary",
    "docker-backend",
    "expressions-contexts-needs-defaults",
    "job-container",
    "microvm-backend",
    "outcome-conclusion-continue-on-error",
    "service-container",
    "shells-and-working-directory",
    "testcontainers",
    "timeouts-cancellation-concurrency",
}
EXECUTION_VALUES = {
    "dual",
    "external-admission-only",
    "hosted-only",
    "secret-gated-dual",
}
DISPOSITION_VALUES = {
    "covered",
    "expected-unsupported",
    "hosted-only",
    "external-admission-only",
}
FIXTURE_STATUS_VALUES = {
    "covered",
    "external-admission-only",
    "hosted-only",
    "incompatible",
    "missing",
    "partial",
}
RUNTIME_SEMANTICS_STATUS_VALUES = {
    "covered",
    "expected-unsupported",
    "incompatible",
    "missing",
    "partial",
}
MICROVM_VALUES = {
    "expected-unsupported",
    "not-applicable-server-expanded",
    "supported",
}
READINESS_ACTION_STATUSES = {
    "covered",
    "external-admission-only",
    "hosted-only",
}
READINESS_RUNTIME_STATUSES = {"covered", "expected-unsupported"}
SURFACE_STATUSES = ("exercised", "expected_unsupported", "admission_only")
SURFACE_KINDS = {"input", "subpath"}

# These are policy exceptions, not alternate defaults. They must stay named
# here so an automatic single-lane path cannot silently become acceptable.
AUTOMATIC_LANE_EXCEPTIONS = {
    ("ci.yml", "pull_request"): "untrusted fork PR has no Velnor trust scope",
    (
        "compat-public-unmerged.yml",
        "pull_request",
    ): "untrusted fork PR has no Velnor trust scope",
}
SECRET_GATED_WORKFLOWS = {
    "app-token-probe.yml": "GitHub App credentials are optional secrets",
}
AUTOMATIC_EVENTS = {"merge_group", "pull_request", "push", "schedule", "workflow_run"}

USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*['\"]?([^'\"\s#]+)")


def load_json(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        failures.append(f"{path.relative_to(ROOT)}: cannot load JSON: {error}")
        return {}
    if not isinstance(value, dict):
        failures.append(f"{path.relative_to(ROOT)}: root must be an object")
        return {}
    return value


def rows_by_key(
    rows: Any,
    key_fields: tuple[str, ...],
    label: str,
    failures: list[str],
) -> dict[tuple[str, ...], dict[str, Any]]:
    result: dict[tuple[str, ...], dict[str, Any]] = {}
    if not isinstance(rows, list):
        failures.append(f"{label}: must be an array")
        return result
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            failures.append(f"{label}[{index}]: must be an object")
            continue
        values = tuple(row.get(field) for field in key_fields)
        if not all(isinstance(value, str) and value for value in values):
            failures.append(
                f"{label}[{index}]: non-empty string key fields required: {key_fields}"
            )
            continue
        if values in result:
            failures.append(f"{label}: duplicate row {values!r}")
            continue
        result[values] = row
    return result


def check_string_list(
    row: dict[str, Any], field: str, label: str, failures: list[str], *, nonempty: bool
) -> list[str]:
    values = row.get(field)
    if not isinstance(values, list) or not all(
        isinstance(value, str) and value for value in values
    ):
        failures.append(f"{label}.{field}: must be an array of non-empty strings")
        return []
    if nonempty and not values:
        failures.append(f"{label}.{field}: must not be empty")
    if len(values) != len(set(values)):
        failures.append(f"{label}.{field}: duplicate values")
    return values


def validate_manifest(
    capabilities: dict[str, Any], failures: list[str]
) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    if capabilities.get("version") != EXPECTED_MANIFEST_VERSION:
        failures.append(
            f"capabilities.version: expected {EXPECTED_MANIFEST_VERSION}, "
            f"got {capabilities.get('version')!r}"
        )
    if capabilities.get("source_sha") != EXPECTED_SOURCE_SHA:
        failures.append(
            f"capabilities.source_sha: expected {EXPECTED_SOURCE_SHA}, "
            f"got {capabilities.get('source_sha')!r}"
        )
    if not isinstance(capabilities.get("crate_version"), str):
        failures.append("capabilities.crate_version: must be a string")

    raw_action_rows = capabilities.get("actions")
    if isinstance(raw_action_rows, list) and len(raw_action_rows) != EXPECTED_ACTION_COUNT:
        failures.append(
            "capabilities.actions: expected exactly "
            f"{EXPECTED_ACTION_COUNT} rows, got {len(raw_action_rows)}"
        )
    raw_workflow_rows = capabilities.get("reusable_workflows")
    if isinstance(raw_workflow_rows, list) and len(raw_workflow_rows) != EXPECTED_REUSABLE_WORKFLOW_COUNT:
        failures.append(
            "capabilities.reusable_workflows: expected exactly "
            f"{EXPECTED_REUSABLE_WORKFLOW_COUNT} rows, got {len(raw_workflow_rows)}"
        )

    action_rows = rows_by_key(
        raw_action_rows, ("repository",), "capabilities.actions", failures
    )
    workflow_rows = rows_by_key(
        raw_workflow_rows,
        ("repository", "path"),
        "capabilities.reusable_workflows",
        failures,
    )
    actions = {key[0]: row for key, row in action_rows.items()}

    if len(actions) != EXPECTED_ACTION_COUNT:
        failures.append(
            f"capabilities.actions: expected {EXPECTED_ACTION_COUNT} rows, got {len(actions)}"
        )
    if len(workflow_rows) != EXPECTED_REUSABLE_WORKFLOW_COUNT:
        failures.append(
            "capabilities.reusable_workflows: expected "
            f"{EXPECTED_REUSABLE_WORKFLOW_COUNT} rows, got {len(workflow_rows)}"
        )

    for repository, row in sorted(actions.items()):
        label = f"capabilities.actions[{repository}]"
        if not isinstance(row.get("adapter"), str) or not row["adapter"]:
            failures.append(f"{label}.adapter: must be a non-empty string")
        check_string_list(row, "allowed_refs", label, failures, nonempty=True)
        check_string_list(row, "allowed_subpaths", label, failures, nonempty=False)
        check_string_list(row, "inputs", label, failures, nonempty=False)

    for key, row in sorted(workflow_rows.items()):
        label = f"capabilities.reusable_workflows[{key[0]}:{key[1]}]"
        check_string_list(row, "allowed_refs", label, failures, nonempty=True)
        check_string_list(row, "inputs", label, failures, nonempty=False)

    return actions, workflow_rows


def validate_coverage_row(
    row: dict[str, Any],
    label: str,
    manifest_row: dict[str, Any],
    failures: list[str],
    *,
    expected_subpaths: Any,
) -> list[str]:
    disposition = row.get("disposition")
    if disposition not in DISPOSITION_VALUES:
        failures.append(f"{label}.disposition: invalid value {disposition!r}")

    reason = row.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        failures.append(f"{label}.reason: must be a non-empty string")

    evidence = check_string_list(row, "evidence", label, failures, nonempty=True)
    for path_text in evidence:
        if not (ROOT / path_text).is_file():
            failures.append(f"{label}.evidence: path does not exist: {path_text}")

    actual_inputs = check_string_list(row, "inputs", label, failures, nonempty=False)
    expected_inputs = manifest_row.get("inputs", [])
    if not isinstance(expected_inputs, list):
        expected_inputs = []
    unknown_inputs = sorted(set(actual_inputs) - set(expected_inputs))
    missing_inputs = sorted(set(expected_inputs) - set(actual_inputs))
    if unknown_inputs:
        failures.append(f"{label}.inputs: unknown values {unknown_inputs}")
    if missing_inputs:
        failures.append(f"{label}.inputs: missing values {missing_inputs}")

    actual_subpaths = check_string_list(row, "subpaths", label, failures, nonempty=False)
    if not isinstance(expected_subpaths, list):
        expected_subpaths = []
    unknown_subpaths = sorted(set(actual_subpaths) - set(expected_subpaths))
    missing_subpaths = sorted(set(expected_subpaths) - set(actual_subpaths))
    if unknown_subpaths:
        failures.append(f"{label}.subpaths: unknown values {unknown_subpaths}")
    if missing_subpaths:
        failures.append(f"{label}.subpaths: missing values {missing_subpaths}")
    return evidence


def validate_coverage(
    coverage: dict[str, Any],
    manifest_actions: dict[str, dict[str, Any]],
    manifest_workflows: dict[tuple[str, str], dict[str, Any]],
    failures: list[str],
    *,
    readiness: bool,
) -> None:
    manifest_identity = coverage.get("manifest")
    if not isinstance(manifest_identity, dict):
        failures.append("coverage.manifest: must be an object")
    else:
        if manifest_identity.get("version") != EXPECTED_MANIFEST_VERSION:
            failures.append(
                f"coverage.manifest.version: expected {EXPECTED_MANIFEST_VERSION}"
            )
        if manifest_identity.get("source_sha") != EXPECTED_SOURCE_SHA:
            failures.append(
                f"coverage.manifest.source_sha: expected {EXPECTED_SOURCE_SHA}"
            )

    raw_action_rows = coverage.get("actions")
    if isinstance(raw_action_rows, list) and len(raw_action_rows) != EXPECTED_ACTION_COUNT:
        failures.append(
            "coverage.actions: expected exactly "
            f"{EXPECTED_ACTION_COUNT} rows, got {len(raw_action_rows)}"
        )
    raw_workflow_rows = coverage.get("reusable_workflows")
    if isinstance(raw_workflow_rows, list) and len(raw_workflow_rows) != EXPECTED_REUSABLE_WORKFLOW_COUNT:
        failures.append(
            "coverage.reusable_workflows: expected exactly "
            f"{EXPECTED_REUSABLE_WORKFLOW_COUNT} rows, got {len(raw_workflow_rows)}"
        )

    coverage_action_rows = rows_by_key(
        raw_action_rows, ("repository",), "coverage.actions", failures
    )
    coverage_actions = {key[0]: row for key, row in coverage_action_rows.items()}
    missing_actions = sorted(set(manifest_actions) - set(coverage_actions))
    unknown_actions = sorted(set(coverage_actions) - set(manifest_actions))
    for repository in missing_actions:
        failures.append(f"coverage.actions: missing row for {repository}")
    for repository in unknown_actions:
        failures.append(f"coverage.actions: unknown action {repository}")

    for repository in sorted(set(manifest_actions) & set(coverage_actions)):
        row = coverage_actions[repository]
        label = f"coverage.actions[{repository}]"
        evidence = validate_coverage_row(
            row,
            label,
            manifest_actions[repository],
            failures,
            expected_subpaths=manifest_actions[repository].get("allowed_subpaths", []),
        )
        execution = row.get("execution")
        status = row.get("fixture_status")
        microvm = row.get("microvm")
        if execution not in EXECUTION_VALUES:
            failures.append(f"{label}.execution: invalid value {execution!r}")
        if status not in FIXTURE_STATUS_VALUES:
            failures.append(f"{label}.fixture_status: invalid value {status!r}")
        if microvm not in MICROVM_VALUES:
            failures.append(f"{label}.microvm: invalid value {microvm!r}")

        expected_microvm = (
            "supported" if repository in MICROVM_SUPPORTED else "expected-unsupported"
        )
        if microvm != expected_microvm:
            failures.append(
                f"{label}.microvm: expected {expected_microvm!r}, got {microvm!r}"
            )

        expected_execution = {
            "actions/create-github-app-token": "secret-gated-dual",
            "actions/deploy-pages": "hosted-only",
            "tailrocks/velnor-actions": "external-admission-only",
        }.get(repository, "dual")
        if execution != expected_execution:
            failures.append(
                f"{label}.execution: expected {expected_execution!r}, got {execution!r}"
            )

        if status in READINESS_ACTION_STATUSES and not evidence:
            if status == "covered":
                failures.append(f"{label}.evidence: covered row requires evidence")
        if readiness and status not in READINESS_ACTION_STATUSES:
            failures.append(f"{label}: readiness status is {status!r}")

    coverage_workflows = rows_by_key(
        raw_workflow_rows,
        ("repository", "path"),
        "coverage.reusable_workflows",
        failures,
    )
    for key in sorted(set(manifest_workflows) - set(coverage_workflows)):
        failures.append(
            f"coverage.reusable_workflows: missing row for {key[0]}:{key[1]}"
        )
    for key in sorted(set(coverage_workflows) - set(manifest_workflows)):
        failures.append(
            f"coverage.reusable_workflows: unknown workflow {key[0]}:{key[1]}"
        )
    for key in sorted(set(manifest_workflows) & set(coverage_workflows)):
        row = coverage_workflows[key]
        label = f"coverage.reusable_workflows[{key[0]}:{key[1]}]"
        validate_coverage_row(
            row,
            label,
            manifest_workflows[key],
            failures,
            expected_subpaths=[],
        )
        if row.get("execution") != "external-admission-only":
            failures.append(f"{label}.execution: must be 'external-admission-only'")
        if row.get("fixture_status") != "external-admission-only":
            failures.append(f"{label}.fixture_status: must be 'external-admission-only'")
        if row.get("microvm") != "not-applicable-server-expanded":
            failures.append(
                f"{label}.microvm: must be 'not-applicable-server-expanded'"
            )

    runtime_rows = rows_by_key(
        coverage.get("runtime_semantics"),
        ("id",),
        "coverage.runtime_semantics",
        failures,
    )
    runtime_ids = {key[0] for key in runtime_rows}
    for runtime_id in sorted(EXPECTED_RUNTIME_SEMANTICS - runtime_ids):
        failures.append(f"coverage.runtime_semantics: missing row for {runtime_id}")
    for runtime_id in sorted(runtime_ids - EXPECTED_RUNTIME_SEMANTICS):
        failures.append(f"coverage.runtime_semantics: unknown row {runtime_id}")
    for key, row in sorted(runtime_rows.items()):
        runtime_id = key[0]
        label = f"coverage.runtime_semantics[{runtime_id}]"
        status = row.get("fixture_status")
        if status not in RUNTIME_SEMANTICS_STATUS_VALUES:
            failures.append(f"{label}.fixture_status: invalid value {status!r}")
        evidence = check_string_list(row, "evidence", label, failures, nonempty=False)
        for path_text in evidence:
            if not (ROOT / path_text).is_file():
                failures.append(f"{label}.evidence: path does not exist: {path_text}")
        if status == "covered" and not evidence:
            failures.append(f"{label}.evidence: covered row requires evidence")
        if status == "expected-unsupported":
            reason = row.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                failures.append(
                    f"{label}.reason: expected-unsupported row requires a non-empty string"
                )
            if not evidence:
                failures.append(
                    f"{label}.evidence: expected-unsupported row requires evidence"
                )
        if readiness and status not in READINESS_RUNTIME_STATUSES:
            failures.append(f"{label}: readiness status is {status!r}")


def workflow_surface_index() -> dict[str, list[dict[str, Any]]]:
    """Index executable remote action references by exact workflow location."""
    result: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(WORKFLOWS.glob("*.yml")):
        relative = path.relative_to(ROOT).as_posix()
        for line, uses, body, uses_indent in extract_uses(path):
            if uses.startswith("./") or "@" not in uses:
                continue
            result.setdefault(uses, []).append(
                {
                    "workflow": relative,
                    "line": line,
                    "inputs": extract_with_inputs(body, uses_indent),
                }
            )
    return result


def surface_reference_identity(reference: str) -> tuple[str, str] | None:
    if "@" not in reference:
        return None
    identity = reference.rsplit("@", 1)[0]
    parts = identity.split("/")
    if len(parts) < 2:
        return None
    return "/".join(parts[:2]), "/".join(parts[2:])


def validate_surface_coverage(
    surface: dict[str, Any],
    manifest_actions: dict[str, dict[str, Any]],
    manifest_workflows: dict[tuple[str, str], dict[str, Any]],
    failures: list[str],
    *,
    verify_workflow_references: bool,
) -> None:
    """Require one explicit disposition for every admitted input/subpath.

    ``fixture-coverage.json`` intentionally retains the manifest-shaped lists
    for human summary. This separate contract is the source of proof: each
    admitted surface item names its disposition and the exact workflow/ref
    that proves it, or an explicit non-execution reason.
    """
    raw_actions = surface.get("actions")
    if not isinstance(raw_actions, list):
        failures.append("surface.actions: must be an array")
        raw_actions = []
    surface_action_rows = rows_by_key(
        raw_actions, ("repository",), "surface.actions", failures
    )
    surface_actions = {key[0]: row for key, row in surface_action_rows.items()}
    for repository in sorted(set(surface_actions) - set(manifest_actions)):
        failures.append(f"surface.actions: unknown action {repository}")
    for repository in sorted(set(manifest_actions) - set(surface_actions)):
        failures.append(f"surface.actions: missing row for {repository}")

    uses = workflow_surface_index() if verify_workflow_references else {}
    for repository in sorted(set(manifest_actions) & set(surface_actions)):
        manifest_row = manifest_actions[repository]
        row = surface_actions[repository]
        label = f"surface.actions[{repository}]"
        expected = {
            ("input", name) for name in manifest_row.get("inputs", [])
        } | {
            ("subpath", name) for name in manifest_row.get("allowed_subpaths", [])
        }
        seen: dict[tuple[str, str], str] = {}
        for status in SURFACE_STATUSES:
            entries = row.get(status)
            if not isinstance(entries, list):
                failures.append(f"{label}.{status}: must be an array")
                continue
            for index, entry in enumerate(entries):
                entry_label = f"{label}.{status}[{index}]"
                if not isinstance(entry, dict):
                    failures.append(f"{entry_label}: must be an object")
                    continue
                kind = entry.get("kind")
                name = entry.get("name")
                if kind not in SURFACE_KINDS or not isinstance(name, str) or not name:
                    failures.append(
                        f"{entry_label}: kind must be input/subpath and name non-empty"
                    )
                    continue
                key = (kind, name)
                if key in seen:
                    failures.append(
                        f"{label}: {key!r} listed in both {seen[key]} and {status}"
                    )
                seen[key] = status
                if key not in expected:
                    failures.append(f"{entry_label}: unknown manifest surface {key!r}")

                reference = entry.get("reference")
                identity = (
                    surface_reference_identity(reference)
                    if isinstance(reference, str)
                    else None
                )
                if identity is None:
                    failures.append(
                        f"{entry_label}.reference: must be repository@reference"
                    )
                    continue
                reference_repository, reference_subpath = identity
                if reference_repository != repository:
                    failures.append(
                        f"{entry_label}.reference: repository must be {repository!r}"
                    )
                allowed_refs = manifest_row.get("allowed_refs", [])
                if reference.rsplit("@", 1)[1] not in allowed_refs:
                    failures.append(
                        f"{entry_label}.reference: unadmitted reference {reference!r}"
                    )

                reason = entry.get("reason")
                if status != "exercised" and (
                    not isinstance(reason, str) or not reason.strip()
                ):
                    failures.append(
                        f"{entry_label}.reason: {status} requires a non-empty reason"
                    )

                workflow = entry.get("workflow")
                if status == "admission_only":
                    if workflow is not None:
                        failures.append(
                            f"{entry_label}.workflow: admission_only must not name an executable workflow"
                        )
                    continue
                if not isinstance(workflow, str) or not workflow:
                    failures.append(
                        f"{entry_label}.workflow: {status} requires a workflow path"
                    )
                    continue
                workflow_path = ROOT / workflow
                if not workflow_path.is_file() or workflow_path.parent != WORKFLOWS:
                    failures.append(
                        f"{entry_label}.workflow: not an executable workflow: {workflow}"
                    )
                    continue
                if not verify_workflow_references:
                    continue
                matching_uses = [
                    use for use in uses.get(reference, []) if use["workflow"] == workflow
                ]
                if not matching_uses:
                    failures.append(
                        f"{entry_label}: reference not found in workflow: {workflow}: {reference}"
                    )
                    continue
                if kind == "subpath" and reference_subpath != name:
                    failures.append(
                        f"{entry_label}.reference: subpath must be {name!r}, got {reference_subpath!r}"
                    )
                if kind == "input" and status == "exercised" and not any(
                    name in use["inputs"] for use in matching_uses
                ):
                    failures.append(
                        f"{entry_label}: input is not passed by the mapped workflow reference"
                    )

        missing = sorted(expected - set(seen))
        for kind, name in missing:
            failures.append(f"{label}: missing surface mapping for {kind} {name}")

    raw_workflows = surface.get("reusable_workflows")
    if raw_workflows is None:
        raw_workflows = []
    surface_workflows = rows_by_key(
        raw_workflows,
        ("repository", "path"),
        "surface.reusable_workflows",
        failures,
    )
    for key in sorted(set(surface_workflows) - set(manifest_workflows)):
        failures.append(f"surface.reusable_workflows: unknown workflow {key[0]}:{key[1]}")
    for key in sorted(set(manifest_workflows) - set(surface_workflows)):
        failures.append(f"surface.reusable_workflows: missing row for {key[0]}:{key[1]}")
    for key in sorted(set(manifest_workflows) & set(surface_workflows)):
        label = f"surface.reusable_workflows[{key[0]}:{key[1]}]"
        row = surface_workflows[key]
        expected = {("input", name) for name in manifest_workflows[key].get("inputs", [])}
        seen: set[tuple[str, str]] = set()
        entries = row.get("admission_only")
        if not isinstance(entries, list):
            failures.append(f"{label}.admission_only: must be an array")
            entries = []
        for index, entry in enumerate(entries):
            entry_label = f"{label}.admission_only[{index}]"
            if not isinstance(entry, dict):
                failures.append(f"{entry_label}: must be an object")
                continue
            kind = entry.get("kind")
            name = entry.get("name")
            key_value = (kind, name)
            if kind != "input" or not isinstance(name, str) or not name:
                failures.append(f"{entry_label}: reusable workflow mappings must name an input")
                continue
            if key_value in seen:
                failures.append(f"{entry_label}: duplicate mapping {key_value!r}")
            seen.add(key_value)
            if key_value not in expected:
                failures.append(f"{entry_label}: unknown manifest surface {key_value!r}")
            if entry.get("workflow") is not None:
                failures.append(f"{entry_label}.workflow: admission_only must be null")
            reference = entry.get("reference")
            identity = (
                surface_reference_identity(reference)
                if isinstance(reference, str)
                else None
            )
            if identity is None or identity[0] != key[0]:
                failures.append(f"{entry_label}.reference: repository must be {key[0]!r}")
            elif isinstance(reference, str) and reference.rsplit("@", 1)[1] not in manifest_workflows[key].get("allowed_refs", []):
                failures.append(f"{entry_label}.reference: unadmitted reference {reference!r}")
            if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
                failures.append(f"{entry_label}.reason: admission_only requires a non-empty reason")
        for missing in sorted(expected - seen):
            failures.append(f"{label}: missing surface mapping for input {missing[1]}")


def validate_kache_contract(
    coverage: dict[str, Any],
    manifest_actions: dict[str, dict[str, Any]],
    failures: list[str],
) -> tuple[str, str]:
    kache = manifest_actions.get("kunobi-ninja/kache-action", {})
    if kache.get("allowed_refs") != [EXPECTED_KACHE_REF]:
        failures.append(
            "capabilities.actions[kunobi-ninja/kache-action].allowed_refs: "
            f"must be [{EXPECTED_KACHE_REF!r}]"
        )
    if "version" not in kache.get("inputs", []):
        failures.append(
            "capabilities.actions[kunobi-ninja/kache-action].inputs: missing 'version'"
        )

    contract = coverage.get("kache_contract")
    if not isinstance(contract, dict):
        failures.append("coverage.kache_contract: must be an object")
        return EXPECTED_KACHE_REF, EXPECTED_KACHE_VERSION
    expected = {
        "repository": "kunobi-ninja/kache-action",
        "ref": EXPECTED_KACHE_REF,
        "version": EXPECTED_KACHE_VERSION,
    }
    if contract != expected:
        failures.append(f"coverage.kache_contract: expected {expected!r}, got {contract!r}")
    return EXPECTED_KACHE_REF, EXPECTED_KACHE_VERSION


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip())


def dispatch_lane_default(text: str) -> tuple[bool, str | None]:
    lines = text.splitlines()
    try:
        dispatch_index = next(
            index
            for index, line in enumerate(lines)
            if re.match(r"^  workflow_dispatch:\s*(?:#.*)?$", line)
        )
    except StopIteration:
        return False, None

    end = len(lines)
    for index in range(dispatch_index + 1, len(lines)):
        line = lines[index]
        if line.strip() and indent_of(line) <= 1:
            end = index
            break

    lane_index = None
    for index in range(dispatch_index + 1, end):
        if re.match(r"^      lanes:\s*(?:#.*)?$", lines[index]):
            lane_index = index
            break
    if lane_index is None:
        return True, None

    for line in lines[lane_index + 1 : end]:
        if line.strip() and indent_of(line) <= 6:
            break
        match = re.match(r"^\s+default:\s*([^#]+?)\s*(?:#.*)?$", line)
        if match:
            return True, match.group(1).strip().strip("'\"")
    return True, None


def extract_uses(path: Path) -> list[tuple[int, str, list[str], int]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    result: list[tuple[int, str, list[str], int]] = []
    for index, line in enumerate(lines):
        match = USES_RE.match(line)
        if not match:
            continue
        uses_indent = indent_of(line)
        boundary_indent = uses_indent
        if not line.lstrip().startswith("-"):
            for previous in reversed(lines[:index]):
                if not previous.strip():
                    continue
                previous_indent = indent_of(previous)
                if previous_indent >= uses_indent:
                    continue
                if previous.lstrip().startswith("-"):
                    boundary_indent = previous_indent
                break
        body: list[str] = []
        for later in lines[index + 1 :]:
            if later.strip() and indent_of(later) <= boundary_indent:
                break
            body.append(later)
        result.append((index + 1, match.group(1), body, uses_indent))
    return result


def extract_with_inputs(body: list[str], uses_indent: int) -> list[str]:
    """Extract direct keys from a step/job ``with`` mapping."""
    for index, line in enumerate(body):
        if line.strip() != "with:":
            continue
        with_indent = indent_of(line)
        inputs: list[str] = []
        for later in body[index + 1 :]:
            if later.strip() and indent_of(later) <= with_indent:
                break
            if not later.strip() or indent_of(later) != with_indent + 2:
                continue
            match = re.match(r"^\s*([A-Za-z0-9_.-]+):(?:\s|$)", later)
            if match:
                inputs.append(match.group(1))
        return inputs
    return []


def validate_used_inputs(
    used_inputs: list[str],
    manifest_row: dict[str, Any],
    label: str,
    failures: list[str],
    *,
    allow_unadmitted: bool = False,
) -> None:
    allowed_inputs = manifest_row.get("inputs", [])
    if not isinstance(allowed_inputs, list):
        allowed_inputs = []
    unknown_inputs = sorted(set(used_inputs) - set(allowed_inputs))
    if unknown_inputs and not allow_unadmitted:
        failures.append(f"{label}: unadmitted action inputs: {unknown_inputs}")


def remote_uses_files() -> list[Path]:
    paths = sorted(WORKFLOWS.glob("*.yml"))
    if ACTIONS.is_dir():
        paths.extend(sorted(ACTIONS.glob("**/action.yml")))
        paths.extend(sorted(ACTIONS.glob("**/action.yaml")))
    return paths


def validate_remote_uses(
    coverage: dict[str, Any],
    manifest_actions: dict[str, dict[str, Any]],
    manifest_workflows: dict[tuple[str, str], dict[str, Any]],
    kache_ref: str,
    kache_version: str,
    failures: list[str],
) -> None:
    workflow_policy = coverage.get("workflow_policy", {})
    negative_workflows: set[str] = set()
    if isinstance(workflow_policy, dict):
        negative = workflow_policy.get("negative", {})
        if isinstance(negative, dict):
            negative_workflows.update(
                name for name in negative if isinstance(name, str)
            )
    expected_negative_raw = (
        workflow_policy.get("expected_negative_uses", {})
        if isinstance(workflow_policy, dict)
        else {}
    )
    expected_negative: dict[str, set[str]] = {}
    if not isinstance(expected_negative_raw, dict):
        failures.append("coverage.workflow_policy.expected_negative_uses: must be an object")
    else:
        for name, values in expected_negative_raw.items():
            if not isinstance(values, list) or not all(
                isinstance(value, str) and value for value in values
            ):
                failures.append(
                    "coverage.workflow_policy.expected_negative_uses"
                    f"[{name!r}]: must be an array of strings"
                )
                continue
            expected_negative[name] = set(values)
            negative_workflows.add(name)

    seen_expected: dict[str, set[str]] = {name: set() for name in expected_negative}

    for path in remote_uses_files():
        relative = path.relative_to(ROOT).as_posix()
        policy_name = path.name if path.parent == WORKFLOWS else relative
        for line_number, uses, body, uses_indent in extract_uses(path):
            if uses.startswith("./") or "@" not in uses:
                continue
            if uses in expected_negative.get(policy_name, set()):
                seen_expected.setdefault(policy_name, set()).add(uses)
                continue

            identity, reference = uses.rsplit("@", 1)
            parts = identity.split("/")
            if len(parts) < 2:
                failures.append(f"{relative}:{line_number}: malformed remote uses: {uses}")
                continue
            repository = "/".join(parts[:2])
            subpath = "/".join(parts[2:])

            if parts[1].lower() == "velnor-actions":
                failures.append(
                    f"{relative}:{line_number}: forbidden velnor-actions execution: {uses}"
                )

            if subpath.startswith(".github/workflows/"):
                row = manifest_workflows.get((repository, subpath))
                if row is None:
                    failures.append(
                        f"{relative}:{line_number}: unknown reusable workflow: {identity}"
                    )
                    continue
                if reference not in row.get("allowed_refs", []):
                    failures.append(
                        f"{relative}:{line_number}: unadmitted reusable workflow ref: {uses}"
                    )
                validate_used_inputs(
                    extract_with_inputs(body, uses_indent),
                    row,
                    f"{relative}:{line_number}",
                    failures,
                )
                continue

            row = manifest_actions.get(repository)
            if row is None:
                failures.append(f"{relative}:{line_number}: unknown action: {identity}")
                continue
            if reference not in row.get("allowed_refs", []):
                failures.append(f"{relative}:{line_number}: unadmitted action ref: {uses}")
            allowed_subpaths = set(row.get("allowed_subpaths", []))
            if (
                subpath
                and subpath not in allowed_subpaths
                and policy_name not in negative_workflows
            ):
                failures.append(
                    f"{relative}:{line_number}: unadmitted action subpath: {identity}"
                )
            validate_used_inputs(
                extract_with_inputs(body, uses_indent),
                row,
                f"{relative}:{line_number}",
                failures,
                allow_unadmitted=policy_name in negative_workflows,
            )

            if repository == "kunobi-ninja/kache-action":
                if reference != kache_ref:
                    failures.append(
                        f"{relative}:{line_number}: Kache ref must be {kache_ref}, got {reference}"
                    )
                version = None
                for body_line in body:
                    version_match = re.match(r"^\s+version:\s*([^#]+?)\s*(?:#.*)?$", body_line)
                    if version_match:
                        version = version_match.group(1).strip().strip("'\"")
                        break
                if version != kache_version:
                    failures.append(
                        f"{relative}:{line_number}: Kache version must be "
                        f"{kache_version}, got {version!r}"
                    )

    for name, expected in sorted(expected_negative.items()):
        missing = sorted(expected - seen_expected.get(name, set()))
        for uses in missing:
            failures.append(
                f"coverage.workflow_policy.expected_negative_uses[{name}]: "
                f"declared reference not found: {uses}"
            )


def workflow_events(text: str) -> set[str]:
    """Return event keys declared in the workflow's top-level ``on`` block."""
    lines = text.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line == "on:")
    except StopIteration:
        return set()
    events: set[str] = set()
    for line in lines[start + 1 :]:
        if line.strip() and indent_of(line) == 0:
            break
        match = re.match(r"^  ([A-Za-z_]+):(?:\s|$)", line)
        if match:
            events.add(match.group(1))
    return events


def event_condition_lines(text: str, event: str) -> list[str]:
    token = re.compile(
        rf"github\.event_name\s*==\s*['\"]{re.escape(event)}['\"]"
    )
    return [line for line in text.splitlines() if token.search(line)]


def has_single_lane_branch(line: str, event: str) -> bool:
    """Detect an event branch whose selected matrix literal has one lane."""
    pattern = re.compile(
        rf"github\.event_name\s*==\s*['\"]{re.escape(event)}['\"]"
        r"[^\n]*?&&\s*['\"]?\[\{\"lane\":\"(GitHub|Velnor)\""
    )
    return bool(pattern.search(line))


def has_single_dispatch_fallback(text: str) -> bool:
    """Detect automatic events falling through to a single Velnor matrix."""
    return bool(
        re.search(
            r"github\.event_name\s*==\s*['\"]workflow_dispatch['\"]"
            r"[^\n]*\|\|[^\n]*\[\{\"lane\":\"Velnor\"",
            text,
        )
    )


def has_dual_lane_evidence(text: str) -> bool:
    lower = text.lower()
    return (
        '"lane":"github"' in lower and '"lane":"velnor"' in lower
    ) or ("'both'" in lower or '"both"' in lower)


def validate_automatic_lane_policy(
    positive: set[str], texts: dict[str, str], failures: list[str]
) -> None:
    for name in sorted(positive):
        text = texts.get(name)
        if text is None:
            continue
        events = workflow_events(text) & AUTOMATIC_EVENTS
        if not events:
            continue
        for event in sorted(events):
            if (name, event) in AUTOMATIC_LANE_EXCEPTIONS:
                continue
            lines = event_condition_lines(text, event)
            if any(has_single_lane_branch(line, event) for line in lines):
                failures.append(
                    f"{name}: automatic {event} path selects one lane; "
                    "only an explicit hosted-only exception may do so"
                )
                continue
            if not lines and has_single_dispatch_fallback(text):
                failures.append(
                    f"{name}: automatic {event} path falls back to one Velnor lane"
                )
                continue
            if lines and not has_dual_lane_evidence("\n".join(lines)):
                failures.append(
                    f"{name}: automatic {event} path has no explicit dual-lane selection"
                )
            elif not lines and not has_dual_lane_evidence(text):
                failures.append(
                    f"{name}: automatic {event} path has no explicit dual-lane selection"
                )


def validate_lane_policy(coverage: dict[str, Any], failures: list[str]) -> None:
    policy = coverage.get("workflow_policy")
    if not isinstance(policy, dict):
        failures.append("coverage.workflow_policy: must be an object")
        return
    positive = policy.get("positive")
    negative = policy.get("negative")
    if not isinstance(positive, list) or not all(
        isinstance(name, str) and name for name in positive
    ):
        failures.append("coverage.workflow_policy.positive: must be an array of strings")
        positive_set: set[str] = set()
    else:
        positive_set = set(positive)
        if len(positive_set) != len(positive):
            failures.append("coverage.workflow_policy.positive: duplicate workflow")
    if not isinstance(negative, dict) or not all(
        isinstance(name, str)
        and name
        and isinstance(reason, str)
        and reason
        for name, reason in negative.items()
    ):
        failures.append(
            "coverage.workflow_policy.negative: must map workflow names to reasons"
        )
        negative_set: set[str] = set()
    else:
        negative_set = set(negative)

    overlap = sorted(positive_set & negative_set)
    for name in overlap:
        failures.append(f"coverage.workflow_policy: workflow classified twice: {name}")

    dispatch_files: set[str] = set()
    defaults: dict[str, str | None] = {}
    for path in sorted(WORKFLOWS.glob("*.yml")):
        has_dispatch, default = dispatch_lane_default(path.read_text(encoding="utf-8"))
        if has_dispatch:
            dispatch_files.add(path.name)
            defaults[path.name] = default

    exception_set = set(SECRET_GATED_WORKFLOWS)
    classified = positive_set | negative_set | exception_set
    for name in sorted(dispatch_files - classified):
        failures.append(f"coverage.workflow_policy: unclassified dispatch workflow: {name}")
    for name in sorted((positive_set | negative_set) - dispatch_files):
        failures.append(
            f"coverage.workflow_policy: classified workflow has no workflow_dispatch: {name}"
        )

    for name in sorted(positive_set & dispatch_files):
        default = defaults[name]
        if default != "both":
            failures.append(
                f".github/workflows/{name}: positive lanes default must be 'both', "
                f"got {default!r}"
            )

    texts = {
        path.name: path.read_text(encoding="utf-8")
        for path in remote_uses_files()
        if path.parent == WORKFLOWS
    }
    for name, reason in sorted(SECRET_GATED_WORKFLOWS.items()):
        if name not in dispatch_files:
            failures.append(f"{name}: secret-gated exception must be workflow_dispatch")
            continue
        text = texts.get(name, "")
        if "secrets." not in text or "if:" not in text:
            failures.append(
                f"{name}: secret-gated exception lacks an explicit secret guard ({reason})"
            )
    validate_automatic_lane_policy(positive_set, texts, failures)


def audit(*, contract_only: bool) -> list[str]:
    failures: list[str] = []
    capabilities = load_json(CAPABILITIES_PATH, failures)
    coverage = load_json(COVERAGE_PATH, failures)
    surface = load_json(SURFACE_COVERAGE_PATH, failures)
    manifest_actions, manifest_workflows = validate_manifest(capabilities, failures)
    validate_surface_coverage(
        surface,
        manifest_actions,
        manifest_workflows,
        failures,
        verify_workflow_references=not contract_only,
    )
    validate_coverage(
        coverage,
        manifest_actions,
        manifest_workflows,
        failures,
        readiness=not contract_only,
    )
    kache_ref, kache_version = validate_kache_contract(
        coverage, manifest_actions, failures
    )
    if not contract_only:
        validate_remote_uses(
            coverage,
            manifest_actions,
            manifest_workflows,
            kache_ref,
            kache_version,
            failures,
        )
        validate_lane_policy(coverage, failures)
    return sorted(set(failures))


def main() -> int:
    args = sys.argv[1:]
    if args not in ([], ["--contract-only"]):
        print("usage: audit_capability_coverage.py [--contract-only]", file=sys.stderr)
        return 2
    contract_only = args == ["--contract-only"]
    failures = audit(contract_only=contract_only)
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        print(f"capability coverage audit failed: {len(failures)} error(s)", file=sys.stderr)
        return 1
    mode = "contract" if contract_only else "readiness"
    print(f"capability coverage {mode} audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
