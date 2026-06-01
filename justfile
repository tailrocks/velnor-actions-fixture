set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

test package:
    cargo test -p "{{package}}"

