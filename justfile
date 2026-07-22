set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

fmt-check:
    cargo fmt --check

clippy package:
    cargo clippy -p "{{package}}" -- -D warnings

nextest package:
    cargo nextest run --locked -p "{{package}}"
