# Velnor Actions Fixture

Small public fixture repository for proving Velnor can execute the GitHub Actions surface used by the first target repositories.

This repository intentionally keeps normal GitHub Actions YAML. It is not a Pkl/KCL experiment.

## Runner Lanes

- `compat-github`: runs on `ubuntu-latest`.
- `compat-velnor`: runs on `[self-hosted, velnor-target-mvp]`.
- `compare-results`: downloads artifacts from both lanes and verifies the normalized outputs match.

## Covered Features

- `actions/checkout`
- `actions/cache`
- `actions/upload-artifact`
- `actions/download-artifact`
- `dtolnay/rust-toolchain`
- `extractions/setup-just`
- `dorny/paths-filter`
- local composite actions
- job outputs and `needs`
- matrix jobs
- command files: `GITHUB_ENV`, `GITHUB_OUTPUT`, `GITHUB_PATH`, `GITHUB_STEP_SUMMARY`
- Docker Buildx setup and local image build

The fixture is deliberately small. It exists to verify execution semantics before running Velnor against larger repositories.
