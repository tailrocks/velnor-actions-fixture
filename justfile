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
