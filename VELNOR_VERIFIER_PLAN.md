# Velnor verifier rearchitecture plan

Status: aligned to the exact verifier branch; coverage redesign waits for the
Velnor capability model and independent architecture review.

## Branch and evidence identity

- Repository: `tailrocks/velnor-actions-fixture`
- Integration branch: `codex/verifier-completion-fixes`
- Starting/verified target SHA: `5c8b57aa64dcbfd8fe6b2f6edae625ae344fc496`
- Velnor under test: `tailrocks/velnor`, branch `perf/docker-rust-mbx`,
  starting/verified target SHA `2858e92df0eb78df4f1a6fe2ad4cbf86f1d56355`
- Shared-branch coordination: worktree isolated from the other lead; fetch
  and reconcile the target remote before commits/pushes. Keep commits small,
  signed off with `git commit -s`, and include
  `Co-authored-by: Codex <codex@openai.com>`.

## Current verifier evidence

- `rtk cargo test --workspace --all-targets --no-fail-fast`: 20 tests across
  15 suites passed on the exact branch.
- This is unit/integration evidence only. No live dual-lane readiness verdict,
  exact deployed image identity, or current Velnor capability audit has been
  accepted.
- `GOAL.md` currently declares a stale Velnor release/manifest baseline;
  derive the capability baseline from the exact Velnor commit under test.

## Target verifier invariants

1. Every positive readiness scenario runs on both GitHub-hosted and Velnor
   lanes unless an explicit, typed exception applies.
2. Evidence is deterministic, machine-readable, live, and carries Velnor
   commit, fixture commit, image digest, lane, scenario, and timestamps/IDs
   only where normalization is justified.
3. Missing, skipped, stale, single-lane, unclassified, or semantically
   divergent evidence fails readiness.
4. Semantic comparison covers observable GitHub behavior, not implementation
   details; normalization is limited to unavoidable identity/time fields.
5. The default Rust scenario uses ordinary Cargo with transparent Velnor mbx;
   explicit sccache and acceleration opt-out are separate scenarios.
6. Capability/action/workflow coverage is generated or validated against the
   exact Velnor manifest and every unsupported input has an explicit negative
   disposition.
7. First-party verifier logic, evidence normalization/comparison, Docker
   probes, audits, and benchmark validation are Rust; YAML and small shell
   fragments remain fixture glue.
8. Negative admission, queue, backend, fault, and diagnostic evidence cannot
   substitute for mandatory dual-lane positive proof.

## Work packages

- V0: exact commit/image identity and capability baseline — P0, active after
  Velnor architecture reports.
- V1: default Rust/mbx, explicit sccache, opt-out, cache interaction, and
  parallel Rust matrix — P1, depends on V0.
- V2: semantic evidence schema/normalization/comparison and live dual-lane
  execution — P0/P1, depends on V0.
- V3: action/reusable workflow/admitted input/subpath coverage and negative
  admission audit — P1, depends on V0.
- V4: cancellation, timeout, post-action, completion, artifact/cache/result,
  and fault/soak scenarios — P0/P1, depends on V2 and Velnor lifecycle model.
- V5: Rust verifier binaries/crates replacing core Python paths — P2, depends
  on stable schemas and audits; no duplicated parallel implementation.
- V6: benchmark result validation and reproducible environment identity — P1,
  depends on V1/V2.
- V7: final independent semantic, performance, reliability, security,
  architecture, coverage, and red-team reviews — required before readiness.

## Required evidence matrix

Track each scenario with: ID, source workflow/action, trigger/input, backend,
trust class, expected support/disposition, hosted evidence, Velnor evidence,
normalization, comparison result, Velnor/fixture/image identity, and failure
diagnostic. Do not edit expected results to hide a Velnor mismatch.

Required Rust rows include default transparent mbx, explicit sccache, opt-out,
Cargo/source persistence, user cache interaction, toolchain/lockfile/feature
changes, build scripts/proc macros/native crates, cross-worktree reuse, and
parallel jobs. Required semantic rows include conditions/status functions,
outcome/conclusion, continue-on-error, outputs/command files, composites,
pre/main/post, failed JS/Docker actions, services/containers, cancellation,
timeouts, artifacts/cache/results, and failure cleanup.

## Gates

Run format, Clippy warnings denied, workspace tests, workflow/capability audits,
negative admission tests, mandatory dual-lane workflows, semantic comparison,
default/compatibility/opt-out Rust lanes, Docker/action lanes, cancellation,
fault, soak, and benchmark validation. Record missing/stale/skipped evidence as
failure. Final evidence must name the exact Velnor commit and image digest.

## Commit/review log

- Plan bootstrap: pending commit/push after remote reconciliation.
- Implementation batches: none accepted.
- Independent reviews: pending.
- Blockers: current Velnor capability model, live runner/hosted evidence, and
  authoritative upstream semantic comparison.
