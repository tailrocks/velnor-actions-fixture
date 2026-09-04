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
  to checkout, cache, and Rust cache. sccache is refused there, not supported.
  Other adapters require an explicit expected-unsupported result with the exact
  reason; that result is not silently counted as dual-lane success.

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

The capability baseline is current Velnor release v0.1.250, manifest version
11. Its content-derived identity is bound to the runner under test at audit
time rather than pinned to constants or a source commit; the source commit it
was taken from remains recorded in the baseline as provenance. Refresh it with
`just refresh-capability-baseline` when capability content changes, never by
hand. The
machine-readable baseline is
`coverage/velnor-capabilities.json`; fixture dispositions and evidence are in
`coverage/fixture-coverage.json`; the source workflow inventory is in
`coverage/source-workflow-inventory.md`.

## Readiness invariants

1. Capability coverage is closed: every action repository and reusable workflow
   the runner under test admits has exactly one coverage row, and every coverage
   row names an identity that runner admits. Citations must contain what they
   cite: a coverage row may only cite a workflow that references its action.
2. Positive workflow dispatch inputs default to `both` and automatic positive
   triggers execute both lanes.
3. No workflow executes an action or reusable workflow from any repository named
   `velnor-actions`; admitted historical identities are admission-only fixtures.
4. Remote identities use admitted immutable refs. The admitted set is compared
   with the runner manifest by identity, never by cardinality: swapping one
   admitted repository for another must fail even though the count is unchanged.
5. `actions/deploy-pages` remains a GitHub-hosted single writer. GitHub App token
   verification is manual and secret-gated. These exceptions must never be
   represented as ordinary dual writers.
6. MicroVM positive coverage is limited to checkout, cache, and Rust cache
   until Velnor admits more guest adapters. Every other action, sccache
   included, has an explicit expected-unsupported microVM disposition.
7. Readiness requires current live evidence from both default lanes, carrying
   provenance that binds it to this run, this fixture commit and this Velnor
   build. Static coverage declarations alone do not prove readiness, and neither
   does evidence that cannot say which run produced it.

## Completion criteria

The repository is ready only when the capability audit, workflow lint, Rust
format/lint/test gates, all negative admission checks, mandatory dual-lane
execution, approved exception evidence, and semantic result comparison pass
for every required scenario. Missing, skipped, stale, hosted-only without an
approved exception, secret-gated without its explicit prerequisite result,
microVM-unsupported without its exact disposition, or unclassified evidence
fails the readiness verdict.
