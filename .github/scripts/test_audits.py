#!/usr/bin/env python3
"""Deterministic regression tests for local workflow and capability policy."""

import argparse
import importlib.util
import json
import tempfile
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


class ManifestContractTests(unittest.TestCase):
    def test_manifest_rejects_old_source_sha(self):
        path = ROOT / "coverage" / "velnor-capabilities.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        old_sha = "738f18f68472c15e30645d81a7d2d664f29e5cab"
        manifest["source_sha"] = old_sha
        failures = []

        coverage_audit.validate_manifest(manifest, failures)

        self.assertIn(
            f"capabilities.source_sha: expected {coverage_audit.EXPECTED_SOURCE_SHA}, "
            f"got {old_sha!r}",
            failures,
        )


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

    def test_recursive_identity_normalization(self):
        value = {
            "lane": "github",
            "result": {
                "runner": "hosted",
                "items": [
                    {"job_id": "github-job", "value": 41},
                    {"observed_at": "2026-08-31T00:00:00Z", "value": 42},
                ],
            },
        }
        self.assertEqual(
            workflow_evidence.normalize(value),
            {"result": {"items": [{"value": 41}, {"value": 42}]}},
        )

    def test_valid_dual_lane_evidence_comparison(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.write_evidence(
                directory,
                "github",
                {"result": "success", "runner": {"name": "hosted"}},
            )
            self.write_evidence(
                directory,
                "velnor",
                {"runner": {"name": "microvm"}, "result": "success"},
            )
            self.assertEqual(self.compare(directory), 0)

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


if __name__ == "__main__":
    unittest.main()
