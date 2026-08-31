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

capability-audit:
    python3 .github/scripts/audit_capability_coverage.py

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
