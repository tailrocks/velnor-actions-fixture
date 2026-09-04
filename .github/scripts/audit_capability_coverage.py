#!/usr/bin/env python3
"""Audit Velnor capability coverage and executable workflow policy.

Stdlib-only by design. ``--contract-only`` validates the two JSON contracts
without requiring the repository's staged workflow migration to be complete.
The default mode is the readiness gate and audits current workflow content.
``--refresh-baseline`` rewrites the cached baseline from the runner under test
and then re-runs that readiness gate, so refreshing is one command and never a
hand edit.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CAPABILITIES_PATH = ROOT / "coverage" / "velnor-capabilities.json"
COVERAGE_PATH = ROOT / "coverage" / "fixture-coverage.json"
SURFACE_COVERAGE_PATH = ROOT / "coverage" / "action-surface-coverage.json"
WORKFLOWS = ROOT / ".github" / "workflows"
ACTIONS = ROOT / ".github" / "actions"

# There are deliberately no EXPECTED_MANIFEST_VERSION / EXPECTED_SOURCE_SHA /
# EXPECTED_ACTION_COUNT constants here. Pinning the baseline to constants is
# what let a v10 baseline certify a v11 runner, and what let one admitted
# action be swapped for another without the audit noticing, because the count
# stayed at 30 across the change. The baseline is now bound to the runner under
# test at audit time and compared by identity, never by cardinality.
#
# Fields of the `velnor capabilities export` document that must agree exactly.
MANIFEST_ACTION_FIELDS = ("adapter", "allowed_refs", "allowed_subpaths", "inputs", "notes")
MANIFEST_WORKFLOW_FIELDS = ("allowed_refs", "inputs", "notes")

# A development build of the runner reports this instead of its commit, because
# `VELNOR_SOURCE_SHA` is only baked in for release builds.
DEVELOPMENT_SOURCE_SHA = "development"

# The exported capability document is a pure function of these four files:
# `manifest.rs` holds every admitted repository, ref, subpath and input;
# `action.rs` names the adapter variants the export prints; `Cargo.toml`
# supplies `crate_version`; `build.rs` decides what `source_sha` becomes. When
# the commit is derived from a checkout's HEAD, an uncommitted change to any of
# them would attribute a manifest to a commit that does not contain it. Other
# uncommitted work in the checkout cannot reach the document and is allowed,
# because a reference checkout under active development is the normal case.
MANIFEST_SOURCE_PATHS = (
    "crates/velnor-runner/src/manifest.rs",
    "crates/velnor-runner/src/action.rs",
    "crates/velnor-runner/build.rs",
    "crates/velnor-runner/Cargo.toml",
)

# `validate_microvm_compiler_cache` (crates/velnor-runner/src/manifest.rs)
# refuses a microVM job that declares `mozilla-actions/sccache-action`, and also
# one carrying any `RUSTC_WRAPPER` or `SCCACHE_*` environment. sccache is
# therefore microVM expected-unsupported, not supported; it was listed here as
# supported, which made the fixture claim proof of something the runner rejects.
MICROVM_SUPPORTED = {
    "actions/cache",
    "actions/checkout",
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
AUTOMATIC_L2_WORKFLOWS = {
    "l2-runtime.yml": "l2-runtime",
    "l2-provenance.yml": "l2-provenance",
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


def load_runner_baseline(
    export_path: Path | None,
    runner_source: Path | None,
    source_sha: str | None,
    failures: list[str],
) -> dict[str, Any] | None:
    """Produce the capability manifest of the Velnor build under test.

    Either a ``velnor-runner capabilities export`` document is supplied
    directly, or a runner checkout is supplied and the export is produced from
    it. Both paths end at the same artefact: a document Velnor wrote about
    itself. Nothing here reads the fixture's checked-in baseline, which is the
    thing being audited.
    """
    if export_path is not None and runner_source is not None:
        failures.append("--capabilities-export and --runner-source are mutually exclusive")
        return None
    if export_path is not None:
        try:
            document = json.loads(export_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            failures.append(f"unreadable capabilities export {export_path}: {error}")
            return None
    elif runner_source is not None:
        document = export_from_runner_source(runner_source, failures)
        if document is None:
            return None
        if source_sha is None:
            source_sha = git_head(runner_source, failures)
            if source_sha is not None:
                require_manifest_sources_committed(runner_source, source_sha, failures)
                if failures:
                    return None
    else:
        failures.append(
            "readiness requires the capability manifest of the Velnor build under test: "
            "pass --capabilities-export PATH (a `velnor-runner capabilities export` "
            "document), or --runner-source DIR (a Velnor checkout), or set "
            "VELNOR_CAPABILITIES_EXPORT / VELNOR_SOURCE_DIR. An audit that cannot see "
            "the runner cannot certify it."
        )
        return None

    if not isinstance(document, dict):
        failures.append("capabilities export: root must be an object")
        return None

    exported_sha = document.get("source_sha")
    if exported_sha == DEVELOPMENT_SOURCE_SHA:
        if not source_sha:
            failures.append(
                "the runner under test is a development build and reports "
                f"source_sha={DEVELOPMENT_SOURCE_SHA!r}; pass --velnor-source-sha SHA "
                "so the baseline is bound to a named commit"
            )
            return None
        document["source_sha"] = source_sha
    elif source_sha and exported_sha != source_sha:
        failures.append(
            f"capabilities export source_sha is {exported_sha!r}, but the commit under "
            f"test is {source_sha!r}; this export came from a different Velnor build"
        )
        return None
    return document


def git_head(directory: Path, failures: list[str]) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        failures.append(f"cannot read the runner commit from {directory}: {result.stderr.strip()}")
        return None
    return result.stdout.strip()


def require_manifest_sources_committed(
    directory: Path, source_sha: str, failures: list[str]
) -> None:
    """Refuse to attribute a working-tree manifest to a commit that lacks it."""
    result = subprocess.run(
        ["git", "-C", str(directory), "status", "--porcelain", "--", *MANIFEST_SOURCE_PATHS],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        failures.append(
            f"cannot read the runner working tree state from {directory}: "
            f"{result.stderr.strip()}"
        )
        return
    dirty = sorted(line[3:].strip() for line in result.stdout.splitlines() if line.strip())
    if dirty:
        failures.append(
            f"the runner checkout has uncommitted changes to {', '.join(dirty)}; the "
            f"exported manifest would not be the manifest of {source_sha}. Commit the "
            "change, or export from the build under test and pass "
            "--capabilities-export with --velnor-source-sha"
        )


def export_from_runner_source(directory: Path, failures: list[str]) -> dict[str, Any] | None:
    """Ask the runner checkout to export its own capability manifest."""
    manifest = directory / "crates" / "velnor-runner" / "src" / "manifest.rs"
    if not manifest.is_file():
        failures.append(f"{directory} is not a Velnor checkout: {manifest} does not exist")
        return None
    # The runner builds with its own pinned toolchain. This fixture pins a
    # different one, and an inherited RUSTUP_TOOLCHAIN silently overrides the
    # runner's rust-toolchain.toml, so the export would describe a build made
    # with the wrong compiler or fail to build at all.
    environment = dict(os.environ)
    environment.pop("RUSTUP_TOOLCHAIN", None)
    result = subprocess.run(
        [
            "cargo",
            "run",
            "--quiet",
            "--locked",
            "-p",
            "velnor-runner",
            "--bin",
            "velnor-runner",
            "--",
            "capabilities",
            "export",
        ],
        cwd=directory,
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    if result.returncode != 0:
        failures.append(
            f"`velnor-runner capabilities export` failed in {directory}: "
            f"{result.stderr.strip()[-2000:]}"
        )
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        failures.append(f"`velnor-runner capabilities export` emitted invalid JSON: {error}")
        return None


def bind_baseline(
    capabilities: dict[str, Any], baseline: dict[str, Any], failures: list[str]
) -> None:
    """Fail loudly on any drift between the checked-in baseline and the runner.

    Comparison is by identity throughout. The admitted action *set* is compared,
    not its size: swapping one repository for another leaves the count
    unchanged and must still fail.
    """
    for field in ("version", "crate_version", "source_sha"):
        expected = baseline.get(field)
        actual = capabilities.get(field)
        if actual != expected:
            failures.append(
                f"coverage/velnor-capabilities.json {field} is {actual!r}, but the Velnor "
                f"build under test reports {expected!r}; the baseline is stale"
            )

    expected_actions = index_export(baseline.get("actions"), ("repository",))
    actual_actions = index_export(capabilities.get("actions"), ("repository",))
    if expected_actions is None or actual_actions is None:
        failures.append("capabilities.actions: both documents must list action objects")
        return
    compare_identity(
        actual_actions, expected_actions, MANIFEST_ACTION_FIELDS, "capabilities.actions", failures
    )

    expected_workflows = index_export(
        baseline.get("reusable_workflows"), ("repository", "path")
    )
    actual_workflows = index_export(
        capabilities.get("reusable_workflows"), ("repository", "path")
    )
    if expected_workflows is None or actual_workflows is None:
        failures.append(
            "capabilities.reusable_workflows: both documents must list workflow objects"
        )
        return
    compare_identity(
        actual_workflows,
        expected_workflows,
        MANIFEST_WORKFLOW_FIELDS,
        "capabilities.reusable_workflows",
        failures,
    )


def index_export(
    rows: Any, key_fields: tuple[str, ...]
) -> dict[tuple[str, ...], dict[str, Any]] | None:
    if not isinstance(rows, list):
        return None
    indexed: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            return None
        key = tuple(str(row.get(field)) for field in key_fields)
        indexed[key] = row
    return indexed


def compare_identity(
    actual: dict[tuple[str, ...], dict[str, Any]],
    expected: dict[tuple[str, ...], dict[str, Any]],
    fields: tuple[str, ...],
    label: str,
    failures: list[str],
) -> None:
    for key in sorted(set(expected) - set(actual)):
        failures.append(
            f"{label}: the runner under test admits {':'.join(key)}, but the baseline "
            "does not list it"
        )
    for key in sorted(set(actual) - set(expected)):
        failures.append(
            f"{label}: the baseline lists {':'.join(key)}, but the runner under test "
            "does not admit it"
        )
    for key in sorted(set(actual) & set(expected)):
        for field in fields:
            if actual[key].get(field) != expected[key].get(field):
                failures.append(
                    f"{label}[{':'.join(key)}].{field}: baseline has "
                    f"{actual[key].get(field)!r}, the runner under test has "
                    f"{expected[key].get(field)!r}"
                )


def validate_manifest(
    capabilities: dict[str, Any], failures: list[str]
) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    """Check the baseline's internal shape. Identity is checked by bind_baseline."""
    if not isinstance(capabilities.get("version"), int):
        failures.append("capabilities.version: must be an integer")
    source_sha = capabilities.get("source_sha")
    if (
        not isinstance(source_sha, str)
        or len(source_sha) != 40
        or not all(character in "0123456789abcdef" for character in source_sha)
    ):
        failures.append(
            "capabilities.source_sha: must be a full lowercase commit SHA naming the "
            f"Velnor build the baseline was taken from, got {source_sha!r}"
        )
    if not isinstance(capabilities.get("crate_version"), str):
        failures.append("capabilities.crate_version: must be a string")

    action_rows = rows_by_key(
        capabilities.get("actions"), ("repository",), "capabilities.actions", failures
    )
    workflow_rows = rows_by_key(
        capabilities.get("reusable_workflows"),
        ("repository", "path"),
        "capabilities.reusable_workflows",
        failures,
    )
    actions = {key[0]: row for key, row in action_rows.items()}

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
    repository: str | None = None,
) -> list[str]:
    disposition = row.get("disposition")
    if disposition not in DISPOSITION_VALUES:
        failures.append(f"{label}.disposition: invalid value {disposition!r}")

    reason = row.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        failures.append(f"{label}.reason: must be a non-empty string")

    evidence = validate_capability_mappings(row, label, failures, repository=repository)

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


def validate_capability_mappings(
    row: dict[str, Any], label: str, failures: list[str], *, repository: str | None = None
) -> list[str]:
    """Require closed producer/comparator/evidence path mappings.

    A citation must contain what it cites. Existence alone was the whole check
    before, which is how 21 action rows came to cite workflow files that never
    mention the action they claim to exercise. A cited workflow or action file
    must reference the repository whose row cites it; other cited files (audit
    scripts, comparators, documentation) only have to exist, because they are
    tooling rather than proof of exercise.
    """
    mappings: dict[str, list[str]] = {}
    for field in ("producer", "comparator", "evidence"):
        values = check_string_list(row, field, label, failures, nonempty=True)
        mappings[field] = values
        for path_text in values:
            path = ROOT / path_text
            if not path.is_file():
                failures.append(f"{label}.{field}: path does not exist: {path_text}")
                continue
            if repository is None or not is_workflow_citation(path_text):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as error:
                failures.append(f"{label}.{field}: unreadable citation {path_text}: {error}")
                continue
            if repository.lower() not in text.lower():
                failures.append(
                    f"{label}.{field}: {path_text} does not reference {repository}; "
                    "a citation must contain what it cites"
                )
    return mappings["evidence"]


def is_workflow_citation(path_text: str) -> bool:
    """True for a citation that claims a workflow or action exercises a row."""
    return path_text.startswith((".github/workflows/", ".github/actions/")) and path_text.endswith(
        (".yml", ".yaml")
    )


def validate_coverage(
    coverage: dict[str, Any],
    manifest_actions: dict[str, dict[str, Any]],
    manifest_workflows: dict[tuple[str, str], dict[str, Any]],
    capabilities_identity: dict[str, Any],
    failures: list[str],
    *,
    readiness: bool,
) -> None:
    manifest_identity = coverage.get("manifest")
    if not isinstance(manifest_identity, dict):
        failures.append("coverage.manifest: must be an object")
    else:
        # The coverage document records which manifest it was written against.
        # That identity is checked against the capability baseline, which is
        # itself bound to the runner under test, so a stale coverage document
        # cannot outlive the build it describes.
        for field in ("version", "source_sha"):
            if manifest_identity.get(field) != capabilities_identity.get(field):
                failures.append(
                    f"coverage.manifest.{field} is {manifest_identity.get(field)!r}, but "
                    f"the capability baseline says {capabilities_identity.get(field)!r}"
                )

    raw_action_rows = coverage.get("actions")
    raw_workflow_rows = coverage.get("reusable_workflows")

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
            repository=repository,
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
            repository=key[0],
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
        evidence = validate_capability_mappings(row, label, failures)
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
        required_markers = (
            "actions/upload-artifact@",
            "app-token-readiness",
            "status=not-ready",
            "status=ready",
            "status=failed",
            "actions/download-artifact@",
        )
        for marker in required_markers:
            if marker not in text:
                failures.append(
                    f"{name}: secret-gated readiness evidence missing {marker!r}"
                )
    validate_automatic_lane_policy(positive_set, texts, failures)
    for workflow_name, job_name in sorted(AUTOMATIC_L2_WORKFLOWS.items()):
        workflow_text = texts.get(workflow_name, "")
        if not re.search(r"^  workflow_call:\s*$", workflow_text, re.MULTILINE):
            failures.append(f"{workflow_name}: automatic verifier path requires workflow_call")
        lane_default = re.search(
            r"^\s+lane:\s+\{[^}]*default:\s*both\b", workflow_text, re.MULTILINE
        )
        if not lane_default:
            failures.append(f"{workflow_name}: workflow_call lane default must be both")
        ci_text = texts.get("ci.yml", "")
        if not re.search(
            rf"^  {re.escape(job_name)}:\s*$.*?^\s+uses:\s+\./\.github/workflows/{re.escape(workflow_name)}\s*$",
            ci_text,
            re.MULTILINE | re.DOTALL,
        ):
            failures.append(
                f"ci.yml: automatic verifier is missing local call for {workflow_name}"
            )
        for dependent_job in ("lane-verdict", "ci-required"):
            body_match = re.search(
                rf"^  {dependent_job}:\n(.*?)(?=^  [A-Za-z0-9_-]+:|\Z)",
                ci_text,
                re.MULTILINE | re.DOTALL,
            )
            if not body_match or not re.search(rf"\b{re.escape(job_name)}\b", body_match.group(1)):
                failures.append(
                    f"ci.yml: {dependent_job} must depend on {job_name}"
                )


def audit(
    *,
    contract_only: bool,
    capabilities_export: Path | None = None,
    runner_source: Path | None = None,
    velnor_source_sha: str | None = None,
) -> list[str]:
    failures: list[str] = []
    capabilities = load_json(CAPABILITIES_PATH, failures)
    coverage = load_json(COVERAGE_PATH, failures)
    surface = load_json(SURFACE_COVERAGE_PATH, failures)
    manifest_actions, manifest_workflows = validate_manifest(capabilities, failures)

    if not contract_only:
        # Readiness binds the checked-in baseline to the Velnor build under
        # test. Without this the baseline is an unverifiable assertion, and a
        # stale one certifies whatever runner happens to be running.
        baseline = load_runner_baseline(
            capabilities_export, runner_source, velnor_source_sha, failures
        )
        if baseline is not None:
            bind_baseline(capabilities, baseline, failures)

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
        capabilities,
        failures,
        readiness=not contract_only,
    )
    if not contract_only:
        validate_remote_uses(
            coverage,
            manifest_actions,
            manifest_workflows,
            failures,
        )
        validate_lane_policy(coverage, failures)
    return sorted(set(failures))


def refresh_baseline(
    *,
    capabilities_export: Path | None,
    runner_source: Path | None,
    velnor_source_sha: str | None,
) -> int:
    """Rewrite the cached baseline from the Velnor build under test.

    The document written is the one the runner produced about itself: it comes
    from ``load_runner_baseline``, the same function readiness uses, and the
    checked-in file is never read, merged into, or partially updated. There is
    therefore no way for a refresh to preserve a value the runner does not
    report. A refresh that produced a document readiness would reject is not a
    refresh, so the readiness gate is re-run afterwards and its failure is this
    command's failure.
    """
    failures: list[str] = []
    baseline = load_runner_baseline(
        capabilities_export, runner_source, velnor_source_sha, failures
    )
    if baseline is None or failures:
        return report(failures or ["the runner under test produced no capability manifest"])

    # The runner's own document must satisfy the shape the audit requires
    # before it is allowed to become the baseline. A development build whose
    # commit was never named is rejected here rather than written out.
    validate_manifest(baseline, failures)
    if failures:
        return report(failures)

    CAPABILITIES_PATH.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")

    # The coverage document records the manifest identity it was written
    # against; readiness compares the two. Leaving it behind would only move
    # the staleness one file across.
    coverage = load_json(COVERAGE_PATH, failures)
    if failures:
        return report(failures)
    coverage["manifest"] = {
        "version": baseline["version"],
        "source_sha": baseline["source_sha"],
    }
    COVERAGE_PATH.write_text(json.dumps(coverage, indent=2) + "\n", encoding="utf-8")

    print(
        "refreshed coverage/velnor-capabilities.json from the runner under test: "
        f"manifest v{baseline['version']}, crate {baseline['crate_version']}, "
        f"source {baseline['source_sha']}"
    )
    failures = audit(
        contract_only=False,
        capabilities_export=capabilities_export,
        runner_source=runner_source,
        velnor_source_sha=velnor_source_sha,
    )
    if failures:
        print(
            "the refreshed baseline does not establish readiness; the coverage "
            "documents still disagree with the runner under test",
            file=sys.stderr,
        )
        return report(failures)
    print("capability coverage readiness audit passed")
    return 0


def report(failures: list[str]) -> int:
    for failure in sorted(set(failures)):
        print(f"ERROR: {failure}", file=sys.stderr)
    print(f"capability coverage audit failed: {len(set(failures))} error(s)", file=sys.stderr)
    return 1


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit Velnor capability coverage against the runner under test. "
            "Readiness mode requires the capability manifest of that runner."
        )
    )
    parser.add_argument(
        "--contract-only",
        action="store_true",
        help="validate the checked-in contracts only; does not establish readiness",
    )
    parser.add_argument(
        "--refresh-baseline",
        action="store_true",
        help=(
            "rewrite coverage/velnor-capabilities.json from the runner under test and "
            "re-run the readiness audit; the only supported way to refresh the baseline"
        ),
    )
    parser.add_argument(
        "--capabilities-export",
        type=Path,
        default=environment_path("VELNOR_CAPABILITIES_EXPORT"),
        help="a `velnor-runner capabilities export` document from the build under test",
    )
    parser.add_argument(
        "--runner-source",
        type=Path,
        default=environment_path("VELNOR_SOURCE_DIR"),
        help="a Velnor checkout to export the capability manifest from",
    )
    parser.add_argument(
        "--velnor-source-sha",
        default=os.environ.get("VELNOR_SOURCE_SHA") or None,
        help="the Velnor commit under test, required for development builds",
    )
    return parser.parse_args(argv)


def environment_path(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(value) if value else None


def main() -> int:
    args = parse_arguments(sys.argv[1:])
    if args.refresh_baseline:
        if args.contract_only:
            print(
                "ERROR: --refresh-baseline and --contract-only are mutually exclusive: "
                "a refresh is defined by the runner under test",
                file=sys.stderr,
            )
            return 1
        return refresh_baseline(
            capabilities_export=args.capabilities_export,
            runner_source=args.runner_source,
            velnor_source_sha=args.velnor_source_sha,
        )
    failures = audit(
        contract_only=args.contract_only,
        capabilities_export=args.capabilities_export,
        runner_source=args.runner_source,
        velnor_source_sha=args.velnor_source_sha,
    )
    if failures:
        return report(failures)
    mode = "contract" if args.contract_only else "readiness"
    print(f"capability coverage {mode} audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
