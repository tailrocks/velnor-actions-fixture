#!/usr/bin/env python3
"""Deterministic regression tests for local workflow and capability policy."""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, filename: str):
    path = ROOT / ".github" / "scripts" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


coverage_audit = load_module("coverage_audit", "audit_capability_coverage.py")
workflow_audit = load_module("workflow_audit", "audit_workflow_surface.py")
workflow_evidence = load_module("workflow_evidence", "workflow_evidence.py")


def load_fixture(name: str):
    path = ROOT / ".github" / "fixtures" / "capability-coverage" / name
    return json.loads(path.read_text(encoding="utf-8"))


class WorkflowPolicyTests(unittest.TestCase):
    def test_ci_reusable_suite_lanes_isolate_fork_pull_requests(self):
        jobs = dict(
            workflow_audit.top_level_jobs(
                (ROOT / ".github" / "workflows" / "ci.yml").read_text()
            )
        )
        suite_jobs = (
            "rust",
            "runtime",
            "actions",
            "docker",
            "l2-runtime",
            "l2-provenance",
        )
        fork_guard = (
            "github.event_name == 'pull_request' && "
            "github.event.pull_request.head.repo.full_name != github.repository"
        )
        fork_github_branch = f"{fork_guard} && 'github'"
        dispatch_branch = "github.event_name == 'workflow_dispatch' && inputs.lanes"
        automatic_both_branches = tuple(
            f"github.event_name == '{event_name}' && 'both'"
            for event_name in ("merge_group", "push", "schedule")
        )

        for job_name in suite_jobs:
            with self.subTest(job=job_name):
                lane = next(
                    line.strip()[len("lane: ") :]
                    for line in jobs[job_name]
                    if line.strip().startswith("lane: ")
                )
                self.assertIn(fork_guard, lane)
                self.assertTrue(lane.startswith(f"${{{{ {fork_github_branch}"))
                self.assertIn(dispatch_branch, lane)
                for branch in automatic_both_branches:
                    self.assertIn(branch, lane)
                self.assertTrue(lane.endswith("|| 'both' }}"))

    def test_hosted_only_exception_accepts_single_quoted_json_matrix(self):
        text = (ROOT / ".github" / "workflows" / "compat-public-unmerged.yml").read_text()
        failures = []
        coverage_audit.validate_hosted_only_pull_request_exception(
            "compat-public-unmerged.yml", "pull_request", text, failures
        )
        self.assertEqual(failures, [])

    def test_required_aggregate_rejects_skipped_compare_after_successful_check(self):
        action = (ROOT / ".github" / "actions" / "aggregate-needs" / "action.yml").read_text()
        self.assertIn("    default: 'false'", action[action.index("  allow-skipped:") :])
        run_start = action.index("      run: |\n") + len("      run: |\n")
        run_lines = []
        for line in action[run_start:].splitlines():
            if line.strip() and not line.startswith("        "):
                break
            run_lines.append(line[8:] if line.startswith("        ") else "")
        script = textwrap.dedent("\n".join(run_lines))
        needs = json.dumps(
            {
                "scheduled-check": {"result": "success"},
                "compare": {"result": "skipped"},
            }
        )
        for name, value in {
            "needs-json": needs,
            "workflow-label": "schedule",
            "allow-skipped": "false",
        }.items():
            script = script.replace(f"${{{{ inputs.{name} }}}}", value)

        with tempfile.TemporaryDirectory() as temporary:
            summary = Path(temporary) / "summary"
            environment = os.environ.copy()
            environment["GITHUB_STEP_SUMMARY"] = str(summary)
            result = subprocess.run(
                ["bash", "-c", script],
                capture_output=True,
                text=True,
                env=environment,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("compare", result.stdout)

        schedule = (ROOT / ".github" / "workflows" / "schedule.yml").read_text()
        self.assertNotIn("allow-skipped: true", schedule[schedule.index("  schedule-required:") :])

    def test_every_compat_required_gate_depends_on_its_comparator(self):
        for workflow_name in ("compat.yml", "compat-public-unmerged.yml"):
            jobs = dict(
                workflow_audit.top_level_jobs(
                    (ROOT / ".github" / "workflows" / workflow_name).read_text()
                )
            )
            required = jobs["compat-required"]
            needs = next(line.strip() for line in required if line.strip().startswith("needs:"))
            self.assertIn("compare-results", needs, workflow_name)
            self.assertIn("if: always()", [line.strip() for line in required])

    def test_required_callable_lane_accepts_string_without_options_or_default(self):
        text = """on:
  workflow_call:
    inputs:
      lane:
        required: true
        type: string
"""
        failures = []
        workflow_audit.check_callable_lane_block(
            "fixture-rust-check.yml", workflow_audit.input_block(text, "lane"), failures
        )
        self.assertEqual(failures, [])

    def test_harness_cargo_test_is_rejected(self):
        text = """jobs:\n  test:\n    steps:\n      - run: |\n          set -euo pipefail\n          cargo test --locked -p fixture-harness --all-targets\n"""
        failures = workflow_audit.cargo_policy_failures({"fixture.yml": text})
        self.assertEqual(len(failures), 1)
        self.assertIn("fixture-harness", failures[0])

    def test_ordinary_cargo_test_remains_allowed(self):
        text = """jobs:\n  test:\n    steps:\n      - run: cargo test --locked -p another-package\n"""
        self.assertEqual(workflow_audit.cargo_policy_failures({"fixture.yml": text}), [])

    def test_evidence_surface_rejects_legacy_records(self):
        path = ROOT / ".github" / "workflows" / "_rust-suite.yml"
        text = path.read_text()
        self.assertEqual(workflow_audit.evidence_schema_failures({path.name: text}), [])

        for marker in ("--bin evidence", 'payload["fields"]'):
            failures = workflow_audit.evidence_schema_failures(
                {path.name: f"{text}\n{marker}\n"}
            )
            self.assertIn("legacy evidence marker", "\n".join(failures))

        missing_collector = text.replace(
            "uses: ./.github/actions/collect-evidence", "uses: ./legacy-evidence"
        )
        failures = workflow_audit.evidence_schema_failures({path.name: missing_collector})
        self.assertIn("shared collector", "\n".join(failures))

    def test_rust_source_change_probe_changes_app_visible_output(self):
        text = (ROOT / ".github" / "workflows" / "_rust-suite.yml").read_text()
        self.assertIn(
            "sed -i 's/format!(\"fixture::{name}\")/format!(\"fixture::source-change::{name}\")/'",
            text,
        )
        self.assertIn("grep -Fxq 'fixture::app-a' baseline.txt", text)
        self.assertIn("grep -Fxq 'fixture::source-change::app-a' rebuilt.txt", text)
        self.assertNotIn("velnor_fixture_marker", text)

    def test_full_sha_audit_checks_list_item_uses(self):
        text = """jobs:\n  test:\n    steps:\n      - uses: actions/checkout@v7\n"""
        failures = workflow_audit.remote_sha_failures({"fixture.yml": text})
        self.assertEqual(len(failures), 1)
        self.assertIn("full-SHA-pinned", failures[0])

    def test_nested_uses_collects_sibling_with_inputs(self):
        path = ROOT / ".github" / "workflows" / "compat.yml"
        dorny = next(
            item
            for item in coverage_audit.extract_uses(path)
            if "dorny/paths-filter@" in item[1]
        )
        self.assertEqual(coverage_audit.extract_with_inputs(dorny[2], dorny[3]), ["filters"])

    def test_pages_policy_requires_dual_evidence_and_hosted_writer(self):
        path = ROOT / ".github" / "workflows" / "pages.yml"
        self.assertEqual(
            workflow_audit.pages_policy_failures({"pages.yml": path.read_text()}), []
        )

    def test_pages_policy_rejects_velnor_writer(self):
        path = ROOT / ".github" / "workflows" / "pages.yml"
        text = path.read_text().replace('"writer":false', '"writer":true')
        failures = workflow_audit.pages_policy_failures({"pages.yml": text})
        self.assertIn("Velnor non-writer marker", "\n".join(failures))

    def test_pages_policy_rejects_mutated_compare_artifact_name(self):
        path = ROOT / ".github" / "workflows" / "pages.yml"
        text = path.read_text().replace(
            "name: pages-evidence-velnor", "name: pages-evidence-other", 1
        )
        failures = workflow_audit.pages_policy_failures({"pages.yml": text})
        self.assertIn("compare must contain both evidence artifact names", "\n".join(failures))

    def test_pages_policy_rejects_velnor_deploy_path(self):
        path = ROOT / ".github" / "workflows" / "pages.yml"
        text = path.read_text()
        old = "github.event_name == 'workflow_dispatch' && inputs.lanes == 'github'"
        prefix, suffix = text.rsplit(old, 1)
        text = prefix + "github.event_name == 'workflow_dispatch'" + suffix
        failures = workflow_audit.pages_policy_failures({"pages.yml": text})
        self.assertIn("only push, GitHub dispatch", "\n".join(failures))


class SurfaceCoverageTests(unittest.TestCase):
    manifest_actions = {
        "actions/checkout": {
            "allowed_refs": [
                "3d3c42e5aac5ba805825da76410c181273ba90b1",
            ],
            "allowed_subpaths": [],
            "inputs": ["persist-credentials"],
        }
    }

    def validate(self, fixture_name=None, fixture=None):
        failures = []
        coverage_audit.validate_surface_coverage(
            fixture if fixture is not None else load_fixture(fixture_name),
            self.manifest_actions,
            {},
            failures,
            verify_workflow_references=True,
        )
        return failures

    def test_valid_fixture_maps_input_to_real_reference(self):
        self.assertEqual(self.validate("valid.json"), [])

    def test_missing_input_mapping_fails_deterministically(self):
        self.assertEqual(
            self.validate("missing-input.json"),
            ["surface.actions[actions/checkout]: missing surface mapping for input persist-credentials"],
        )

    def test_expected_unsupported_is_not_exercised(self):
        fixture = load_fixture("valid.json")
        entry = fixture["actions"][0]["exercised"].pop()
        entry["reason"] = "Not supported by the microVM adapter."
        fixture["actions"][0]["expected_unsupported"].append(entry)
        self.assertEqual(self.validate(fixture=fixture), [])


class BaselineBindingTests(unittest.TestCase):
    """The baseline must be bound to the runner under test, by identity.

    Before this, the baseline was pinned to Python constants: a v10 baseline
    certified a v11 runner, and one admitted action was swapped for another
    without the audit noticing, because the count stayed at 30.
    """

    def baseline(self):
        path = ROOT / "coverage" / "velnor-capabilities.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def bind(self, runner):
        failures = []
        coverage_audit.bind_baseline(self.baseline(), runner, failures)
        return failures

    def test_the_checked_in_baseline_matches_itself(self):
        self.assertEqual(self.bind(self.baseline()), [])

    def test_a_stale_manifest_version_is_rejected(self):
        runner = self.baseline()
        runner["version"] = runner["version"] + 1
        self.assertIn("the baseline is stale", "\n".join(self.bind(runner)))

    def test_an_unrelated_source_commit_does_not_change_capability_identity(self):
        runner = self.baseline()
        runner["source_sha"] = "2fad3ffbd3f813f1b504de14163f9b57799b5e8c"
        self.assertEqual(self.bind(runner), [])

    def test_a_tampered_capability_identity_is_rejected(self):
        runner = self.baseline()
        runner[coverage_audit.CAPABILITY_ID_FIELD] = "0" * coverage_audit.CAPABILITY_ID_LENGTH
        failures = "\n".join(self.bind(runner))
        self.assertIn("capability_id", failures)

    def test_capability_identity_excludes_only_source_commit_and_identity(self):
        document = self.baseline()
        identity = document[coverage_audit.CAPABILITY_ID_FIELD]
        document["source_sha"] = "2fad3ffbd3f813f1b504de14163f9b57799b5e8c"
        self.assertEqual(coverage_audit.capability_identity(document), identity)
        document[coverage_audit.CAPABILITY_ID_FIELD] = "0" * coverage_audit.CAPABILITY_ID_LENGTH
        self.assertEqual(coverage_audit.capability_identity(document), identity)
        document["crate_version"] = "0.1.251"
        self.assertNotEqual(coverage_audit.capability_identity(document), identity)

    def test_a_swapped_action_identity_is_rejected_at_constant_cardinality(self):
        """A constant-cardinality action identity swap must fail the audit."""
        runner = self.baseline()
        original = runner["actions"][0]["repository"]
        runner["actions"][0]["repository"] = "example/not-admitted-action"
        self.assertEqual(len(runner["actions"]), len(self.baseline()["actions"]))
        failures = "\n".join(self.bind(runner))
        self.assertIn("example/not-admitted-action", failures)
        self.assertIn(original, failures)

    def test_a_widened_allowed_ref_is_rejected(self):
        runner = self.baseline()
        runner["actions"][0]["allowed_refs"] = runner["actions"][0]["allowed_refs"] + [
            "0000000000000000000000000000000000000000"
        ]
        self.assertIn("allowed_refs", "\n".join(self.bind(runner)))

    def test_a_widened_input_surface_is_rejected(self):
        runner = self.baseline()
        runner["actions"][0]["inputs"] = runner["actions"][0]["inputs"] + ["smuggled"]
        self.assertIn("inputs", "\n".join(self.bind(runner)))

    def test_content_drift_with_a_recomputed_identity_is_rejected(self):
        """A forged well-formed identity cannot authorize a changed surface."""
        runner = self.baseline()
        runner["actions"][0]["allowed_subpaths"] = runner["actions"][0][
            "allowed_subpaths"
        ] + ["actions/not-admitted"]
        runner[coverage_audit.CAPABILITY_ID_FIELD] = coverage_audit.capability_identity(
            runner
        )
        failures = "\n".join(self.bind(runner))
        self.assertIn("allowed_subpaths", failures)
        self.assertIn("actions/not-admitted", failures)

    def test_readiness_without_a_runner_baseline_fails(self):
        failures = []
        coverage_audit.load_runner_baseline(None, None, None, failures)
        self.assertIn("cannot certify it", "\n".join(failures))

    def test_a_development_build_must_name_its_commit(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "export.json"
            document = self.baseline()
            document["source_sha"] = coverage_audit.DEVELOPMENT_SOURCE_SHA
            path.write_text(json.dumps(document), encoding="utf-8")
            failures = []
            self.assertIsNone(coverage_audit.load_runner_baseline(path, None, None, failures))
            self.assertIn("development build", "\n".join(failures))

    def test_an_export_from_another_commit_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "export.json"
            path.write_text(json.dumps(self.baseline()), encoding="utf-8")
            failures = []
            self.assertIsNone(
                coverage_audit.load_runner_baseline(
                    path, None, "0" * 40, failures
                )
            )
            self.assertIn("different Velnor build", "\n".join(failures))


class SourceWorkflowInventoryTests(unittest.TestCase):
    def inventory(self):
        path = ROOT / "coverage" / "source-workflow-inventory.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_stale_source_workflow_digest_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            runner_source = Path(temporary)
            workflow_dir = runner_source / ".github" / "workflows"
            workflow_dir.mkdir(parents=True)
            (workflow_dir / "ci.yml").write_text("name: ci\n", encoding="utf-8")
            inventory = {
                "schema": coverage_audit.SOURCE_WORKFLOW_INVENTORY_SCHEMA,
                "source_sha": "a" * 40,
                "workflows": [
                    {
                        "path": ".github/workflows/ci.yml",
                        "sha256": "0" * 64,
                        "uses": [],
                        "fixture_workflows": ["ci.yml"],
                    }
                ],
                "action_mappings": [],
            }
            failures = []
            coverage_audit.validate_source_workflow_inventory(
                inventory,
                runner_source=runner_source,
                source_sha="a" * 40,
                failures=failures,
            )

        self.assertIn("ci.yml changed", "\n".join(failures))

    def test_checked_in_inventory_has_explicit_action_mappings(self):
        inventory = self.inventory()
        failures = []
        coverage_audit.validate_source_workflow_inventory(
            inventory,
            runner_source=None,
            source_sha=inventory["source_sha"],
            failures=failures,
        )
        self.assertEqual(failures, [])


class MicroVmDispositionTests(unittest.TestCase):
    """A microVM claim must match what the runner will actually admit."""

    def test_sccache_is_not_claimed_microvm_supported(self):
        # crates/velnor-runner/src/manifest.rs validate_microvm_compiler_cache
        # refuses a microVM job declaring this action, and equally one carrying
        # a RUSTC_WRAPPER or SCCACHE_* environment.
        self.assertNotIn(
            "mozilla-actions/sccache-action", coverage_audit.MICROVM_SUPPORTED
        )

    def test_every_microvm_disposition_matches_the_supported_set(self):
        coverage = json.loads(
            (ROOT / "coverage" / "fixture-coverage.json").read_text(encoding="utf-8")
        )
        for row in coverage["actions"]:
            expected = (
                "supported"
                if row["repository"] in coverage_audit.MICROVM_SUPPORTED
                else "expected-unsupported"
            )
            self.assertEqual(row["microvm"], expected, row["repository"])


class RunnerCheckoutStateTests(unittest.TestCase):
    """A commit may only name a manifest the commit actually contains."""

    def checkout(self, temporary):
        directory = Path(temporary)
        run = lambda *args: subprocess.run(  # noqa: E731
            ["git", "-C", str(directory), *args], check=True, capture_output=True
        )
        run("init", "--quiet")
        run("config", "user.email", "fixture@example.invalid")
        run("config", "user.name", "fixture")
        for relative in coverage_audit.MANIFEST_SOURCE_PATHS:
            path = directory / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("committed\n", encoding="utf-8")
        run("add", "--all")
        run("commit", "--quiet", "-m", "fixture")
        return directory, run

    def test_a_clean_manifest_source_tree_is_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory, _ = self.checkout(temporary)
            failures = []
            coverage_audit.require_manifest_sources_committed(directory, "0" * 40, failures)
            self.assertEqual(failures, [])

    def test_unrelated_uncommitted_work_is_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory, _ = self.checkout(temporary)
            (directory / "crates" / "velnor-runner" / "src" / "runner.rs").write_text(
                "work in progress\n", encoding="utf-8"
            )
            failures = []
            coverage_audit.require_manifest_sources_committed(directory, "0" * 40, failures)
            self.assertEqual(failures, [])

    def test_an_uncommitted_manifest_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory, _ = self.checkout(temporary)
            (directory / "crates" / "velnor-runner" / "src" / "manifest.rs").write_text(
                "uncommitted\n", encoding="utf-8"
            )
            failures = []
            coverage_audit.require_manifest_sources_committed(directory, "0" * 40, failures)
            self.assertIn("manifest.rs", "\n".join(failures))
            self.assertIn("would not be the manifest of", "\n".join(failures))


class CitationTests(unittest.TestCase):
    """A citation must contain what it cites."""

    def row(self, evidence):
        return {
            "producer": [".github/scripts/audit_capability_coverage.py"],
            "comparator": [".github/scripts/audit_capability_coverage.py"],
            "evidence": evidence,
        }

    def test_a_workflow_that_does_not_mention_the_action_is_rejected(self):
        failures = []
        coverage_audit.validate_capability_mappings(
            self.row([".github/workflows/_rust-suite.yml"]),
            "coverage.actions[fsfe/reuse-action]",
            failures,
            repository="fsfe/reuse-action",
        )
        self.assertIn("does not reference fsfe/reuse-action", "\n".join(failures))

    def test_a_workflow_that_does_mention_the_action_is_accepted(self):
        failures = []
        coverage_audit.validate_capability_mappings(
            self.row([".github/workflows/_rust-suite.yml"]),
            "coverage.actions[mozilla-actions/sccache-action]",
            failures,
            repository="mozilla-actions/sccache-action",
        )
        self.assertEqual(failures, [])

    def test_every_checked_in_citation_contains_what_it_cites(self):
        coverage = json.loads(
            (ROOT / "coverage" / "fixture-coverage.json").read_text(encoding="utf-8")
        )
        failures = []
        for row in coverage["actions"]:
            coverage_audit.validate_capability_mappings(
                row,
                f"coverage.actions[{row['repository']}]",
                failures,
                repository=row["repository"],
            )
        self.assertEqual(failures, [])


class WorkflowEvidenceTests(unittest.TestCase):
    def write_evidence(self, directory, lane, semantic):
        path = directory / f"{lane}.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "velnor.fixture.control-plane.v1",
                    "scenario": "success",
                    "evidence_id": "default",
                    "lane": lane,
                    "runner_name": f"{lane}-runner",
                    "semantic": semantic,
                }
            ),
            encoding="utf-8",
        )

    def compare(self, directory):
        return workflow_evidence.compare(
            argparse.Namespace(
                directory=str(directory),
                scenario="success",
                lanes=["github", "velnor"],
            )
        )

    def test_semantic_payload_is_compared_verbatim(self):
        """Nothing inside `semantic` is normalized, at any depth.

        The previous implementation dropped every object key named `lane`,
        `runner`, `run_id`, `job_id` or `observed_at` at any depth, so a
        divergence nested under such a key vanished before comparison.
        """
        record = {
            "semantic": {
                "lane": "github",
                "result": {"runner": "hosted", "items": [{"job_id": "a", "value": 41}]},
            }
        }
        self.assertEqual(
            workflow_evidence.semantic_payload(record), record["semantic"]
        )

    def test_valid_dual_lane_evidence_comparison(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for lane in ("github", "velnor"):
                self.write_evidence(directory, lane, {"result": "success"})
            self.assertEqual(self.compare(directory), 0)

    def test_divergence_nested_under_a_key_named_runner_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.write_evidence(directory, "github", {"runner": {"exit_code": 0}})
            self.write_evidence(directory, "velnor", {"runner": {"exit_code": 7}})
            with self.assertRaisesRegex(
                SystemExit, r"semantic evidence mismatch.*runner\.exit_code"
            ):
                self.compare(directory)

    def test_a_single_lane_comparison_is_an_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.write_evidence(directory, "velnor", {"result": "success"})
            with self.assertRaisesRegex(SystemExit, "requires at least two lanes"):
                workflow_evidence.compare(
                    argparse.Namespace(
                        directory=str(directory), scenario="success", lanes=["velnor"]
                    )
                )

    def test_diagnose_never_claims_parity(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.write_evidence(directory, "velnor", {"result": "success"})
            self.assertEqual(
                workflow_evidence.diagnose(
                    argparse.Namespace(
                        directory=str(directory), scenario="success", lanes=["velnor"]
                    )
                ),
                0,
            )

    def test_missing_lane_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.write_evidence(directory, "github", {"result": "success"})
            with self.assertRaisesRegex(SystemExit, "lane evidence mismatch"):
                self.compare(directory)

    def test_semantic_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.write_evidence(directory, "github", {"result": "success"})
            self.write_evidence(directory, "velnor", {"result": "failure"})
            with self.assertRaisesRegex(
                SystemExit, r"semantic evidence mismatch.*\$\.result"
            ):
                self.compare(directory)


class CompareEvidenceActionTests(unittest.TestCase):
    """The comparator binds Velnor evidence to the build that produced it."""

    def action_text(self):
        return (ROOT / ".github" / "actions" / "compare-evidence" / "action.yml").read_text()

    def resolver_script(self):
        action = self.action_text()
        start = action.index("        python3 - ", action.index("Resolve comparison identities"))
        body_start = action.index("\n", start) + 1
        body_end = action.index("\n        PY", body_start)
        return textwrap.dedent(action[body_start:body_end])

    def run_resolver(self, records):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            directory = temporary / "evidence"
            directory.mkdir()
            for relative, record in records:
                path = directory / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(record), encoding="utf-8")
            github_env = temporary / "github-env"
            environment = os.environ.copy()
            environment["GITHUB_ENV"] = str(github_env)
            with github_env.open("w", encoding="utf-8") as handle:
                result = subprocess.run(
                    [sys.executable, "-", str(directory)],
                    cwd=ROOT,
                    input=self.resolver_script(),
                    stderr=subprocess.PIPE,
                    stdout=handle,
                    text=True,
                    env=environment,
                )
            environment_values = dict(
                line.split("=", 1)
                for line in github_env.read_text(encoding="utf-8").splitlines()
                if line
            )
            return result, environment_values

    @staticmethod
    def record(lane, source_sha=None):
        provenance = {"lane": lane}
        if source_sha is not None:
            provenance["velnor_source_sha"] = source_sha
        return {"provenance": provenance}

    def test_evidence_source_must_match_checked_in_baseline(self):
        current_source = "d" * 40
        baseline_source = json.loads(
            (ROOT / "coverage" / "velnor-capabilities.json").read_text()
        )["source_sha"]
        self.assertNotEqual(current_source, baseline_source)
        result, output = self.run_resolver(
            [
                ("github.json", self.record("github")),
                ("nested/velnor-a.json", self.record("velnor", current_source)),
                ("nested/velnor-b.json", self.record("velnor", current_source)),
            ]
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output, {})
        self.assertIn("does not match capability baseline source_sha", result.stderr)
        self.assertIn(current_source, result.stderr)
        self.assertIn(baseline_source, result.stderr)

    def test_evidence_source_matching_checked_in_baseline_is_accepted(self):
        baseline_source = json.loads(
            (ROOT / "coverage" / "velnor-capabilities.json").read_text()
        )["source_sha"]
        result, output = self.run_resolver(
            [
                ("github.json", self.record("github")),
                ("nested/velnor-a.json", self.record("velnor", baseline_source)),
                ("nested/velnor-b.json", self.record("velnor", baseline_source)),
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            output,
            {
                "BASELINE_MANIFEST_VERSION": "12",
                "EVIDENCE_VELNOR_SOURCE_SHA": baseline_source,
            },
        )

    def test_missing_velnor_source_identity_fails_closed(self):
        result, output = self.run_resolver(
            [
                ("github.json", self.record("github")),
                ("velnor.json", self.record("velnor")),
            ]
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output, {})
        self.assertIn("provenance.velnor_source_sha", result.stderr)

    def test_mixed_velnor_source_identities_fail_closed(self):
        first_source = "a" * 40
        second_source = "b" * 40
        result, output = self.run_resolver(
            [
                ("velnor-a.json", self.record("velnor", first_source)),
                ("nested/velnor-b.json", self.record("velnor", second_source)),
            ]
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output, {})
        self.assertIn("mixed provenance.velnor_source_sha", result.stderr)
        self.assertIn(first_source, result.stderr)
        self.assertIn(second_source, result.stderr)

    def test_non_commit_velnor_source_identity_fails_closed(self):
        result, output = self.run_resolver(
            [("velnor.json", self.record("velnor", "development"))]
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output, {})
        self.assertIn("full lowercase commit SHA", result.stderr)

    def test_action_passes_derived_source_to_the_verifier(self):
        action = self.action_text()
        self.assertIn(
            '--expect-velnor-source-sha "${EVIDENCE_VELNOR_SOURCE_SHA}"', action
        )
        self.assertIn('baseline_source_sha = baseline.get("source_sha")', action)
        self.assertIn("if source_sha != baseline_source_sha:", action)

    def test_action_wires_github_env_handoff_before_verifier_step(self):
        action = self.action_text()
        resolver_start = action.index("- name: Resolve comparison identities")
        compare_start = action.index("- name: Compare observed lane behaviour")
        self.assertLess(resolver_start, compare_start)
        resolver = action[resolver_start:compare_start]
        self.assertIn("COMPARE_DIRECTORY: ${{ inputs.directory }}", resolver)
        self.assertIn(
            'python3 - "${COMPARE_DIRECTORY}" >> "${GITHUB_ENV}" <<\'PY\'',
            resolver,
        )
        self.assertIn(
            'print(f"BASELINE_MANIFEST_VERSION={manifest_version}")', resolver
        )
        self.assertIn(
            'print(f"EVIDENCE_VELNOR_SOURCE_SHA={source_sha}")', resolver
        )
        compare = action[compare_start:]
        self.assertIn(
            '--expect-velnor-source-sha "${EVIDENCE_VELNOR_SOURCE_SHA}"', compare
        )


if __name__ == "__main__":
    unittest.main()
