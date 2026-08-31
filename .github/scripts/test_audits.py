#!/usr/bin/env python3
"""Deterministic regression tests for local workflow and capability policy."""

import importlib.util
import json
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


def load_fixture(name: str):
    path = ROOT / ".github" / "fixtures" / "capability-coverage" / name
    return json.loads(path.read_text(encoding="utf-8"))


class WorkflowPolicyTests(unittest.TestCase):
    def test_harness_cargo_test_is_rejected(self):
        text = """jobs:\n  test:\n    steps:\n      - run: |\n          set -euo pipefail\n          cargo test --locked -p fixture-harness --all-targets\n"""
        failures = workflow_audit.cargo_policy_failures({"fixture.yml": text})
        self.assertEqual(len(failures), 1)
        self.assertIn("fixture-harness", failures[0])

    def test_ordinary_cargo_test_remains_allowed(self):
        text = """jobs:\n  test:\n    steps:\n      - run: cargo test --locked -p another-package\n"""
        self.assertEqual(workflow_audit.cargo_policy_failures({"fixture.yml": text}), [])

    def test_nested_uses_collects_sibling_with_inputs(self):
        path = ROOT / ".github" / "workflows" / "compat.yml"
        dorny = next(
            item
            for item in coverage_audit.extract_uses(path)
            if "dorny/paths-filter@" in item[1]
        )
        self.assertEqual(coverage_audit.extract_with_inputs(dorny[2], dorny[3]), ["filters"])


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


if __name__ == "__main__":
    unittest.main()
