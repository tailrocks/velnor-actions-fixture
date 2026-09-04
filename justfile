set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

fmt-check:
    cargo fmt --check

clippy package:
    cargo clippy -p "{{package}}" -- -D warnings

nextest package:
    cargo nextest run --locked -p "{{package}}"

python-check:
    python3 -c 'import ast; from pathlib import Path; paths=sorted(Path(".github/scripts").rglob("*.py")); assert paths, "no Python scripts found"; [ast.parse(path.read_text(encoding="utf-8"), filename=str(path)) for path in paths]'

python-test:
    python3 .github/scripts/test_audits.py

# Readiness requires the capability manifest of the Velnor build under test.
# Set VELNOR_CAPABILITIES_EXPORT to a `velnor-runner capabilities export`
# document, or VELNOR_SOURCE_DIR to a Velnor checkout. An audit that cannot see
# the runner cannot certify it, and now says so instead of passing.
capability-audit:
    python3 .github/scripts/audit_capability_coverage.py

# The only supported way to refresh the cached baseline. It rewrites
# coverage/velnor-capabilities.json from the Velnor build under test and then
# re-runs the readiness gate above, so a refresh that does not certify is not a
# refresh. Never edit that file by hand; the readiness gate rejects any content
# the runner does not report anyway.
#
#   VELNOR_SOURCE_DIR=/path/to/velnor just refresh-capability-baseline
#
# A development build reports source_sha "development"; the recipe names the
# checkout's HEAD commit for provenance. Capability binding uses the content
# digest, so unrelated runner commits do not invalidate unchanged admissions.
refresh-capability-baseline:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${VELNOR_SOURCE_DIR:-}" && -z "${VELNOR_SOURCE_SHA:-}" ]]; then
      VELNOR_SOURCE_SHA="$(git -C "${VELNOR_SOURCE_DIR}" rev-parse HEAD)"
      export VELNOR_SOURCE_SHA
    fi
    python3 .github/scripts/audit_capability_coverage.py --refresh-baseline

# Contract-only mode checks the checked-in documents against each other. It
# does not establish readiness and must never be substituted for the gate above.
capability-contract:
    python3 .github/scripts/audit_capability_coverage.py --contract-only

audit-workflows:
    python3 .github/scripts/audit_workflow_surface.py

rust-check:
    cargo check --workspace --all-targets --locked

rust-test:
    cargo nextest run --workspace --locked

l2-closure:
    cargo run --locked -p l2-contract -- validate

workflow-check:
    actionlint
    just python-check
    just python-test
    ! rg -n '^\s*-\s*uses:.*tailrocks/velnor-actions' .github/workflows

check:
    just capability-audit
    just workflow-check
    just audit-workflows
    just fmt-check
    just rust-check
    just rust-test
    just l2-closure
