# Velnor Actions Fixture

Small public fixture repository for proving Velnor can execute the GitHub Actions surface used by the first target repositories.

This repository intentionally keeps normal GitHub Actions YAML. It is not a Pkl/KCL experiment.

## Runner Lanes

- `lanes=velnor` (default): runs on `[self-hosted, velnor-target-mvp]`.
- `lanes=github`: runs on pinned `ubuntu-26.04`.
- `lanes=both`: expands the same jobs on both runners from one inline matrix.
- `compare-results`: downloads artifacts from both lanes and verifies the normalized outputs match.

## Covered Features

- `actions/checkout`
- `actions/cache`
- `actions/upload-artifact`
- `actions/download-artifact`
- local-only sccache, Kache, and compiler-cache-off selection
- `dorny/paths-filter`
- local composite actions
- job outputs and `needs`
- matrix jobs
- command files: `GITHUB_ENV`, `GITHUB_OUTPUT`, `GITHUB_PATH`, `GITHUB_STEP_SUMMARY`
- Docker Buildx setup and local image build
- Postgres service health, alias reachability, and mapped-port context

## Build L2 proof corpus

Plan 013 adds three explicit, manually dispatched workflows:

- `l2-runtime.yml` executes the same locked Rust, recursive closure, mise, and
  cache corpus on GitHub-hosted and Velnor lanes.
- `l2-negative.yml` proves mutable action references are classified before its
  marker can run.
- `l2-provenance.yml` creates a deterministic subject on both lanes, compares
  checksums first, then verifies exact source and signer attestations on a
  hosted consumer.

The checked-in closure is validated by the dependency-free `l2-contract`
crate. Run the complete local gate with `mise run check`.

The fixture is deliberately small. It exists to verify execution semantics before running Velnor against larger repositories.

## License

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
