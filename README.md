# Velnor Actions Fixture

Small public fixture repository for proving Velnor can execute the GitHub Actions surface used by the first target repositories.

This repository intentionally keeps normal GitHub Actions YAML. It is not a Pkl/KCL experiment.

## Runner Lanes

- `lanes=both` (mandatory default): runs the same local suite on GitHub
  `ubuntu-26.04` and the Velnor trusted runner `[self-hosted,
  velnor-target-mvp]`.
- `lanes=github` or `lanes=velnor`: explicit diagnostic single-lane dispatch;
  it never claims parity.
- `verifier compare` requires both lane artifacts, rejects evidence that does not
  belong to the current run and Velnor build, and treats a single lane as an error.

`ci.yml` is self-contained: `_rust-suite.yml`, `_runtime-suite.yml`,
`_actions-suite.yml`, and `_docker-suite.yml` are local reusable workflows.
There are no remote reusable workflow calls. Public untrusted PRs are the
explicit hosted-only exception. Pages deployment remains hosted-only with one
writer; mutation/secret-gated jobs and Velnor-only negative admission and
queue/backend diagnostics retain their explicit conditions.

## Readiness classes

Mandatory positive scenarios require semantic evidence from both runners. The
only exceptions are explicit and must produce their own evidence:

- Hosted-only: untrusted fork pull requests and the single
  `actions/deploy-pages` writer. Pages build/upload/compare still run on both
  lanes.
- Secret-gated dual: GitHub App-token verification runs on both lanes when the
  required credentials exist; otherwise the workflow reports a skipped
  prerequisite, not readiness.
- MicroVM expected-unsupported: Velnor microVM supports positive checkout,
  cache, Rust cache, and sccache only. Other adapters need an explicit reason
  for expected-unsupported status.

Velnor-only admission negatives, queue probes, and backend diagnostics are
diagnostic checks, not substitutes for mandatory dual-lane proof.

## Verifier surfaces

- `fixture-rust-check.yml` is a local reusable workflow. `reuse-caller.yml`
  calls it for `app-a` and `app-b` on explicit GitHub and Velnor lanes;
  `result-*.json` artifacts and `verifier compare` require every package and
  lane result when `lanes=both`. Single-lane dispatch is diagnostic.
- `schedule.yml` runs the fixture harness on both lanes and compares normalized
  semantic evidence in a hosted job.
- `backend-parity.yml` records explicit backend identity: `github-hosted` for
  GitHub and `docker` or `microvm` for Velnor; its hosted comparator checks the
  remaining semantic evidence.
- `multi-arch.yml` builds and tests `linux/amd64` and `linux/arm64` on each
  selected lane; its hosted comparator requires all four records and compares
  each platform.
- `control-plane.yml` compares normalized lane evidence with the repository-
  local comparator. Queue is the explicit queue exception, guarded and
  Velnor-only; failure is the expected exception and its logs must contain
  exactly one marked `controlled-failure` error.
- `docker-lease-probe.yml` uses the repository-local raw-wire helper
  `.github/scripts/workflow_evidence.py docker-probe` and compares per-lane
  Docker lease evidence in a hosted job.
- `attestation-negative.yml` uses `assert-negative` to assert the expected
  per-lane failure or success conclusion for each negative attestation case.

The local `check` gate runs capability coverage, workflow-surface and
actionlint checks, side-effect-free Python syntax parsing, Rust formatting,
workspace compilation, tests, and the L2 closure check. Run it with
`mise run check` or `just check`.

## Control Plane

`control-plane.yml` is a manually dispatched corpus for Velnor control-plane
validation: deterministic success, a deliberate failure at exactly one named
step, externally cancellable holds, queue isolation, measurable job overlap,
bounded sanitized artifacts, cold/warm cache evidence, and bounded load with
guaranteed teardown.

Every phase emits machine-readable `::notice::CP_MARKER scenario=... phase=...`
lines plus plain `KEY=value` echo lines. A hosted aggregator reports the
requested terminal state versus the observed state and exits nonzero only on an
unexpected mismatch; for `scenario=failure` the controlled failure at the named
`controlled-failure` step is the requested outcome. The aggregator additionally
parses each `scenario-failure` job log and proves exactly one
`::error::CP_MARKER` line was emitted, that it carries
`phase=controlled-failure ... expected=true`, and that the terminal marker
followed — acceptance for this scenario is log-based (CP_MARKER parsing), with
no artifact handoff.

### Inputs

| Input | Type | Default | Allowed | Notes |
| --- | --- | --- | --- | --- |
| `scenario` | choice | `success` | `success`, `failure`, `hold`, `queue`, `concurrent`, `artifacts`, `cache`, `load` | Exactly one scenario per dispatch |
| `hold_seconds` | number | `30` | `0..300` | Validated in-step; out-of-range fails fast |
| `artifact_count` | number | `3` | `1..8` | Validated in-step; distinct bounded sanitized text artifacts |
| `lanes` | choice | `both` | `github`, `velnor`, `both` | Canonical plural lanes selector |

Scenario notes:

- `hold`: sleeps `hold_seconds`; designed to be cancelled through GitHub.
- `queue`: targets runs-on label `velnor-cp-queue-validation`. No other runner
  in the fleet carries that label; only one dedicated ephemeral validation
  instance may register it, so this job stays queued until that instance picks
  it up. **Prerequisite:** register exactly that ephemeral runner before
  dispatching this scenario. A queued job's `timeout-minutes` bounds only its
  execution after dequeue (10 minutes here), never the queued wait itself, so
  the hosted `queue-guard` job bounds the wait instead: it polls for up to 210
  seconds for `scenario-queue` to leave the queued state and exits green as
  soon as it does; if no dedicated runner dequeues it, the guard emits a
  `queue-still-queued` mismatch marker, cancels the run, and exits nonzero —
  guarded fail-fast instead of an unbounded QUEUED hang.
- `concurrent`: two matrix jobs each hold ~20s; the aggregator proves interval
  overlap from emitted epoch timestamps.
- `cache`: fixed cache key `cp-control-plane-<os>-fixed-v1`; an unchanged rerun
  expects `CP_CACHE_HIT=true`.
- `load`: nproc-bounded CPU loop, 256 MiB bounded memory touch, 64 MiB bounded
  disk write, declared measurement tolerances, and teardown that runs even on
  cancellation.

### Dispatch cleanup rules

Before every dispatch: cancel all non-completed `control-plane` and `compat`
runs (`gh run cancel`) and delete only stale runner registrations whose name
carries the dedicated validation prefix (`velnor-cp-queue-validation`),
confirming none remains. Never save rendered GitHub HTML while inspecting runs;
record run URLs and sanitized JSON only. A `queue` dispatch without the
dedicated runner self-resolves through the queue-guard cancellation above;
still confirm zero non-completed runs remain afterwards.

## Covered Features

- `actions/checkout`
- `actions/cache`
- `actions/upload-artifact`
- `actions/download-artifact`
- local-only sccache, Mr Boxington, and compiler-cache-off selection
- `dorny/paths-filter`
- local composite actions
- job outputs and `needs`
- matrix jobs
- command files: `GITHUB_ENV`, `GITHUB_OUTPUT`, `GITHUB_PATH`, `GITHUB_STEP_SUMMARY`
- Docker Buildx setup and local image build
- Postgres service health, alias reachability, and mapped-port context
- deterministic Pages docs-tree validation: missing or empty trees fail; a
  tree containing a non-empty regular file passes

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

The current baseline is Velnor v0.1.250, manifest v11, at source commit
`9f522e5f638f15d934544c07d382afb7adf0c472`; see the [baseline/source workflow
inventory](coverage/source-workflow-inventory.md).

`coverage/velnor-capabilities.json` is not an independent assertion: it is a
cached copy of what `velnor-runner capabilities export` emits, and the capability
audit re-binds it to the runner under test on every readiness run. Supply that
runner with `VELNOR_CAPABILITIES_EXPORT` (an export document) or
`VELNOR_SOURCE_DIR` (a Velnor checkout); without one, readiness fails rather than
passing on a baseline nobody checked.

Evidence records carry provenance the workflow cannot fabricate — run id, run
attempt, commit, lane cross-checked against `RUNNER_ENVIRONMENT`, runner
identity, the Velnor build identity, and a collection timestamp — and every
compared value is measured by `verifier collect` rather than written into the
workflow. See `VELNOR_VERIFIER_PLAN.md`.

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
