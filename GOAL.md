# Velnor Readiness Verifier Goal

This repository is the self-contained readiness verifier for
[`tailrocks/velnor`](https://github.com/tailrocks/velnor). It must exercise the
GitHub Actions workloads that Velnor customers use and compare their observable
results with the same workloads on GitHub-hosted runners.

## Required outcome

- Keep every executable fixture workflow, local action, Rust example, test
  payload, and comparison tool in this repository. Runtime verification must not
  depend on `*/velnor-actions` workflows or actions.
- Run every mandatory positive readiness scenario on both a Velnor runner and
  a GitHub-hosted runner by default. Single-lane dispatches are diagnostic and
  cannot establish readiness.
- Emit deterministic evidence from each lane and fail when either lane is
  missing or their normalized semantic results differ.
- Cover every action identity, reusable workflow, admitted input, admitted
  subpath, runtime behavior, and execution backend exposed by Velnor's strict
  capability manifest. Every unsupported surface must have an explicit negative
  test or documented disposition; silent gaps are forbidden.
- Use Rust examples and integration/functional tests as workload payloads,
  including build scripts, command files, expressions, outputs, caches,
  artifacts, services, containers, Docker builds, releases, Pages, provenance,
  cancellation, concurrency, and failure semantics.

## Readiness classes

Mandatory dual-lane scenarios emit comparable semantic evidence from the same
fixture on GitHub-hosted and Velnor runners. A missing, skipped, or divergent
lane fails readiness unless the scenario is one of the explicit classes below.

- Hosted-only: an untrusted fork pull request cannot enter Velnor's trusted
  scope. Pages build, upload, and comparison remain dual-lane; only the
  `actions/deploy-pages` writer runs on the hosted runner.
- Secret-gated dual: GitHub App-token verification is manual and runs on both
  lanes only when its required credentials exist. Missing credentials produce
  an explicit prerequisite result, never a readiness pass.
- MicroVM expected-unsupported: Velnor microVM positive execution is limited
  to checkout, cache, Rust cache, and sccache. Other adapters require an
  explicit expected-unsupported result with the exact reason; that result is
  not silently counted as dual-lane success.

Velnor-only admission negatives, queue probes, and backend diagnostics are
diagnostic evidence. They do not replace mandatory dual-lane positive proof.

## Source estate

Coverage is derived from GitHub Actions usage in:

- `ChainArgos/java-monorepo`
- `tailrocks/velnor`
- `jackin-project/jackin`
- `jackin-project/homebrew-tap`
- `jackin-project/jackin-the-architect`
- `tailrocks/ruxel`
- `tailrocks/holla`
- `tailrocks/termrock`
- `tailrocks/parallax`
- `tailrocks/tablerock`
- `tailrocks/schemalane`

The capability baseline is Velnor manifest version 10 at source commit
`738f18f68472c15e30645d81a7d2d664f29e5cab`. The machine-readable baseline is
`coverage/velnor-capabilities.json`; fixture dispositions and evidence are in
`coverage/fixture-coverage.json`.

## Readiness invariants

1. Capability coverage is closed: exactly 30 admitted action repositories and
   two admitted reusable workflows have one coverage row each.
2. Positive workflow dispatch inputs default to `both` and automatic positive
   triggers execute both lanes.
3. No workflow executes an action or reusable workflow from any repository named
   `velnor-actions`; admitted historical identities are admission-only fixtures.
4. Remote identities use admitted immutable refs. Kache uses
   `kunobi-ninja/kache-action@49398d37113c616fdb61be434cb497e3c2c8f3e6`
   with `version: v0.14.2`.
5. `actions/deploy-pages` remains a GitHub-hosted single writer. GitHub App token
   verification is manual and secret-gated. These exceptions must never be
   represented as ordinary dual writers.
6. MicroVM positive coverage is limited to checkout, cache, Rust cache, and
   sccache until Velnor admits more guest adapters. Every other action has an
   explicit expected-unsupported microVM disposition.
7. Readiness requires current live evidence from both default lanes. Static
   coverage declarations alone do not prove readiness.

## Completion criteria

The repository is ready only when the capability audit, workflow lint, Rust
format/lint/test gates, all negative admission checks, mandatory dual-lane
execution, approved exception evidence, and semantic result comparison pass
for every required scenario. Missing, skipped, stale, hosted-only without an
approved exception, secret-gated without its explicit prerequisite result,
microVM-unsupported without its exact disposition, or unclassified evidence
fails the readiness verdict.
