set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

fmt-check:
    cargo fmt --check

clippy package:
    cargo clippy -p "{{package}}" -- -D warnings

test package:
    cargo test -p "{{package}}"

nextest package:
    cargo nextest run -p "{{package}}"
