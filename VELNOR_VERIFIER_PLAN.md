# Velnor verifier rearchitecture plan

Status: synchronized to the Velnor capability model and independent
architecture review; the current capability baseline is manifest v12.

## Branch and evidence identity

- Repository: `tailrocks/velnor-actions-fixture`
- Integration branch: `codex/verifier-completion-fixes`
- Last verified fixture SHA: `62fc276ec4c99524e43fa9c9fa9e40f04a04aef3`
- Velnor under test: `tailrocks/velnor`, branch `perf/docker-rust-mbx`,
  verified target SHA `c57786af83a65428ca697cf5867abcdc26eb9539`
- Shared-branch coordination: worktree isolated from the other lead; fetch
  and reconcile the target remote before commits/pushes. Keep commits small,
  signed off with `git commit -s`, and include
  `Co-authored-by: Codex <codex@openai.com>`.

## Current verifier evidence

- The supported capability refresh against the target above passed, and the
  contract audit plus 50 verifier Python tests pass. A full `mise run check`
  has not been rerun at this identity.
- This is unit/integration evidence only. No live dual-lane readiness verdict,
  exact deployed image identity, or current Velnor capability audit has been
  accepted.
- The checked-in capability baseline is generated from the Velnor runner under
  test; its content identity and source provenance must be revalidated whenever
  the runner capability surface changes.

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

---

# V-1 — the verifier is not an oracle (P0)

This section is the concrete, finding-level execution plan for work package V0
and the evidence half of V2. Every claim below was verified against both trees
before any code changed.

## Current synchronized state

| Tree | Branch | Commit |
| --- | --- | --- |
| `velnor-actions-fixture` (last verified) | `codex/verifier-completion-fixes` | `62fc276ec4c99524e43fa9c9fa9e40f04a04aef3` |
| `velnor` (runner under test) | `perf/docker-rust-mbx` | `c57786af83a65428ca697cf5867abcdc26eb9539` |

The manifest identity recorded below is the identity of the runner under test;
refresh the checked-in export whenever that target changes.

## Problem statement

The fixture is supposed to be an oracle: it must be able to observe a Velnor
runner behaving differently from a GitHub-hosted runner and say so. It cannot.
Every one of the six findings below was verified against the two trees before
any code was changed.

### F1 — cross-lane comparison is vacuous (verified)

Every field fed into the cross-lane comparators is a literal written in the
workflow YAML, so both lanes emit byte-identical JSON by construction.

- `crates/fixture-harness/src/bin/evidence.rs:51` collects `--field key=value`
  strings from the command line and `:60-65` copies them verbatim into the
  record. Nothing is observed.
- Every caller passes literals:
  `.github/workflows/_rust-suite.yml:79-81`,
  `_actions-suite.yml:91-94`, `_runtime-suite.yml:168-171`,
  `_docker-suite.yml:78-81`, `schedule.yml:80-81`,
  `backend-parity.yml:98-100`, `compat.yml:169-171`,
  `compat-public-unmerged.yml:159-161`.
- `.github/scripts/write-result.py:14-24` is the same defect in Python: the
  whole `result.json` payload — package, label, evidence, `runtime.os`,
  `runtime.shell` — is a hard-coded dictionary.
- The only two environment-derived fields in the estate are
  `multi-arch.yml:107` (`digest`) and `backend-parity.yml:99` (`backend`), and
  `backend-parity.yml:166-167` deletes `backend` from both records immediately
  before comparing them.

Consequence: the comparators can fail only when a lane artifact is missing.
They cannot fail on behavior.

### F2 — stale evidence establishes readiness (verified)

`audit()` (`.github/scripts/audit_capability_coverage.py:1139-1171`) reads
three checked-in JSON files plus workflow text and nothing else. Evidence
validation is `(<repo root> / path).is_file()`
(`audit_capability_coverage.py:274-286`). There is no run id, no run attempt,
no commit, no timestamp and no API call anywhere in the audit. Evidence
produced by any past run, or against any other Velnor build, certifies the
current one.

### F3 — the capability baseline was stale and could not detect it (closed)

The original audit pinned a manifest version and source SHA in Python while
never reading Velnor. It now requires a live export or runner source, binds the
checked-in JSON to that identity, and fails closed when the source is absent or
stale. The current checked-in export is manifest v12 at the synchronized runner
commit recorded above.

### F4 — cardinality cannot detect identity drift (closed)

The audit now binds the checked-in export to the runner under test by action
and reusable-workflow identity, refs, subpaths, and inputs. Its mutation test
replaces one admitted action with an absent identity while preserving row
count; the audit reports both sides of the drift.

### F5 — false-coverage rows (verified, and larger than reported)

The audit reported seven rows whose `evidence` citations do not contain what
they cite. Cross-checking every action row in `coverage/fixture-coverage.json`
against the workflow files that actually reference each repository shows
**21** rows with at least one false workflow citation, including
`fsfe/reuse-action` and `crazy-max/ghaction-github-runtime` citing
`_rust-suite.yml` (which mentions neither), `docker/login-action` and
`docker/bake-action` citing `_docker-suite.yml` (which mentions neither), and
`jackin-project/jackin-role-action` citing `_actions-suite.yml` when the
repository is referenced by no workflow at all. `is_file()` is the entire
citation check, so a citation only has to name a file that exists.

### F6 — normalization hides divergence (verified)

`compare-results.py:16` drops `lane`, `runner` and `runner_name` and
`:70-79` applies that drop **recursively at every depth** of the document, so
any nested subtree keyed by one of those names disappears from the comparison.
`workflow_evidence.py:15-17` does the same for `lane`, `runner`,
`runner_name`, `run_id`, `job_id` and `observed_at`, applied recursively at
`:20-30`. `workflow_evidence.py:118-123` returns `0` with the message
"parity not claimed" when only one lane is present, without comparing
anything — a silent success.

## Target architecture

Three properties, each enforced by a distinct mechanism.

### A. Baseline binding (fixes F3, F4)

`coverage/velnor-capabilities.json` stops being an independent assertion and
becomes a *cached copy* of a Velnor-produced document, checked against the
runner under test at audit time.

- Source of truth is `velnor capabilities export`
  (`crates/velnor-runner/src/manifest.rs:1652-1700`), which already emits
  `version`, `source_sha`, `crate_version`, and every admitted action and
  reusable workflow with its refs, subpaths and inputs.
- The audit takes `--capabilities-export PATH` (a live export artifact) or
  `--runner-source PATH` (the runner checkout, from which the manifest
  identity and admitted set are parsed). Readiness mode requires one of them;
  `--contract-only` remains available for the internal consistency check.
- The comparison is **set identity**, not cardinality: the admitted action
  repository set, the reusable workflow `(repository, path)` set, and each
  row's `allowed_refs` / `allowed_subpaths` / `inputs` must match exactly.
  `EXPECTED_ACTION_COUNT` and `EXPECTED_REUSABLE_WORKFLOW_COUNT` are deleted.
- `EXPECTED_MANIFEST_VERSION` and `EXPECTED_SOURCE_SHA` are deleted; identity
  comes from the export and mismatch is a loud failure naming both sides.
- Obsolete generic compiler-cache action coverage is removed because the
  runner no longer admits that identity.

### B. Collected evidence with provenance (fixes F1, F2, F5)

A typed evidence record replaces the free-form `--field key=value` bag.

```
schema      velnor.fixture.evidence.v2
scenario    string
evidence_id string
provenance  run_id, run_attempt, run_number, repository, commit_sha,
            workflow, job, lane, runner_name, runner_os, runner_arch,
            runner_environment, image_digest?, velnor_manifest_version?,
            velnor_source_sha?, collected_at
observed    ordered map of observation name -> observation
```

- Provenance is read from the GitHub-provided environment by the collector,
  never from an argument. A missing required variable is a hard error, so a
  record cannot be produced outside a real job.
- Observations are *collected*: process exit codes, step outcomes and
  conclusions passed in as the GitHub-computed `steps` context, environment
  variable effects, digests of files the job produced, and parsed command-file
  results. There is no way to state an observation as a literal.
- Readiness rejects a record whose provenance is absent or incomplete, whose
  `run_id`/`run_attempt` is not the current run, whose `commit_sha` is not the
  commit under test, or whose Velnor identity differs from the runner under
  test.
- Citations must contain what they cite: the audit requires each cited
  workflow or action file to actually reference the action repository whose
  row cites it. `external-admission-only` rows cite the admission fixture that
  proves the identity is rejected, not an unrelated suite.

### C. A comparison that can fail (fixes F1, F6)

- Normalization becomes an explicit typed allowlist of *fully qualified*
  fields. Only runner identity (`provenance.runner_name`,
  `provenance.lane`, `provenance.runner_environment`), run identifiers
  (`provenance.run_id`, `provenance.run_attempt`, `provenance.run_number`,
  `provenance.job`) and timestamps (`provenance.collected_at`) qualify. The
  `observed` subtree is compared verbatim, at every depth.
- Recursive key-name dropping is deleted from both Python comparators.
- A single-lane compare is an error. Diagnostic single-lane dispatch keeps a
  separate, explicitly named verb that never prints a parity claim.

### D. Mutation discipline (fixes the root cause)

The bug class behind all six findings is that nothing ever tested the verifier
by feeding it wrong input. Every comparator and readiness check gains a
mutation test that constructs deliberately wrong evidence and asserts
rejection: stale run, wrong commit, missing lane, divergent observed outcome,
fabricated provenance, drifted manifest identity, false citation.

## Task list and completion conditions

| ID | Task | Complete when |
| --- | --- | --- |
| V-1.a | This plan, committed and pushed first | On `origin/codex/verifier-completion-fixes` |
| V-1.b1 | Delete `EXPECTED_MANIFEST_VERSION`, `EXPECTED_SOURCE_SHA`, `EXPECTED_ACTION_COUNT`, `EXPECTED_REUSABLE_WORKFLOW_COUNT`; bind the baseline to a live export or runner source | Audit fails loudly against a stale baseline and passes against a current export derived from the runner |
| V-1.b2 | Replace cardinality with set identity for actions and reusable workflows | Swapping one repository for another in either document fails the audit |
| V-1.b3 | Remove the obsolete compiler-cache action contract and its `compat.yml` step; refresh the baseline to current identity | No removed-action reference remains in scripts, coverage or workflows |
| V-1.c1 | Typed `EvidenceRecord` v2 with collected provenance in Rust | `evidence collect` refuses to emit outside a job context |
| V-1.c2 | Observations are collected, not stated | No `--field` literal path remains for observed values |
| V-1.c3 | Readiness rejects stale / wrong-commit / provenance-free records | Mutation tests V-1.e pass |
| V-1.c4 | Citations must contain what they cite; fix all 21 false rows | Audit passes with the citation check enabled |
| V-1.d1 | Typed allowlist normalization replacing recursive subtree dropping | A divergence nested under a key named `runner` is reported |
| V-1.d2 | Single-lane compare is an error in both comparators | Exit code is non-zero with one lane present |
| V-1.e | Mutation tests for every rejection above | `cargo nextest run --workspace` and `just python-test` cover each case |

## Rust / Python split

Per the scope limit, the whole Python verifier is **not** ported. The split:

- **Rust now** — `crates/verifier`: the evidence record, provenance
  collection, provenance verification, the typed allowlist comparator and all
  mutation tests. This is where the type system does real work.
- **Python now, Rust later** — `audit_capability_coverage.py` baseline
  binding, set-identity comparison and the citation check. These are edits to
  an existing 1200-line auditor; rewriting it is out of scope for V-1.
  **Slated for the Rust port:** `validate_manifest`, `validate_coverage`,
  `validate_surface_coverage`, `validate_capability_mappings` and the baseline
  binding introduced here. The Python architecture is not grown: no new
  Python modules are added.
- **Python deleted** — `write-result.py` (literal payload author) is replaced
  by the Rust collector rather than repaired.

## V-1 status

All twelve tasks are complete on `codex/verifier-completion-fixes`.

The `--field key=value` mechanism is deleted, not deprecated: the
`fixture-harness` `Evidence` type and its `evidence` binary are gone, so no
workflow can author an evidence value any more. Every one of the nine
producers now uses `.github/actions/collect-evidence`, and every comparator
uses `.github/actions/compare-evidence`. `write-result.py` and
`compare-results.py` are deleted.

The one deliberate exception is `backend-parity.yml`. Its execution backend
legitimately differs between lanes — that is what the workflow exists to prove
— so the backend is asserted per lane against its admitted set instead of being
deleted from both records immediately before comparison, as it was. What is
compared across lanes is the workload's observed behaviour despite the
different backend.

Gates run locally, all green: `just check` (capability readiness audit,
actionlint, Python syntax, 31 Python tests, workflow-surface audit, `cargo fmt
--check`, `cargo check --workspace --all-targets --locked`, 49 workspace tests
including 16 mutation tests, L2 closure), plus `cargo clippy --workspace
--all-targets --locked -- -D warnings`.

## Out of scope for V-1

The native Rust scenario matrix (Velnor's default acceleration versus explicit
sccache) is untouched. It is a separate package of work; this task only
removes the false all-clear that hid the manifest change which introduced it.

# V-3 — refreshing the baseline, and the coverage it was blocking (P0)

## Historical starting state

V-1 bound the checked-in baseline to the runner under test, and the readiness
gate was correctly failing:

```
ERROR: coverage/velnor-capabilities.json source_sha is
'2858e92df0eb78df4f1a6fe2ad4cbf86f1d56355', but the Velnor build under test
reports '63bbc3f48e1c0ea226cc55014e1268953f254cb3'; the baseline is stale
```

Comparing the runner's own `capabilities export` against the checked-in
document showed the failure was **only** the commit: manifest version,
`crate_version`, the admitted action set, the reusable workflow set and every
row's refs, subpaths and inputs already agreed exactly. The old capability
identity transition had already been landed by V-1. The baseline now comes
from the runner export, and the mutation test deliberately replaces one
action identity to prove cardinality alone cannot certify it.

## F7 — a refresh nobody could perform without a hand edit (verified)

The gate could say a baseline was stale but nothing could make it current. Three
consecutive commits on this branch (`7bdcfcf`, `1225edc`, `378405c`) do nothing
but retype a commit SHA in four or five files each, which is precisely the hand
edit the gate exists to make impossible. A hand edit cannot turn a stale
baseline into a correct one; it can only turn it into a wrong one that happens
to satisfy one field.

`just refresh-capability-baseline` replaces that. It exports the manifest from
the build under test through the same `load_runner_baseline` the readiness gate
uses, writes that document verbatim, carries the manifest identity into
`coverage/fixture-coverage.json`, and re-runs readiness: a refresh that does not
certify is not a refresh. The checked-in file is never read or merged into, so
no value can survive a refresh that the runner does not report. Deriving the
commit from a checkout's HEAD additionally requires `manifest.rs`, `action.rs`,
`build.rs` and `Cargo.toml` to be committed — those four files are exactly what
the exported document is derived from, and attributing them to a commit that
does not contain them is the same staleness in a smaller window. Unrelated work
in the checkout stays allowed, because a shared reference checkout under active
development is the normal case.

Two prose statements of the baseline commit (`README.md`, `GOAL.md`) are deleted
rather than updated. A commit SHA restated in documentation is a copy that can
only go stale; the baseline records it once.

## F8 — the fixture claimed microVM supports sccache (verified)

`validate_microvm_compiler_cache` (`crates/velnor-runner/src/manifest.rs`)
refuses a microVM job that declares `mozilla-actions/sccache-action`, and
equally one carrying any `RUSTC_WRAPPER` or `SCCACHE_*` environment. The
coverage row recorded `microvm: supported` and `MICROVM_SUPPORTED` listed the
action, so the audit enforced the false claim instead of catching it —
`_rust-suite.yml` already documented the opposite in a comment. The row is now
`expected-unsupported` with the runner's own reason, and a test holds every
microVM disposition to the supported set.

## F9 — generic compiler-cache action backend contract (closed)

The original F9 found that the pinned `jdx/mr-boxington-action` rejected the
fixture's `backend: local` selection. The compatibility workflow now selects
the supported `github` backend, while manifest v12 constrains the action to its
pinned identity and supported backend/input contract.

Velnor declares the action as `ActionAdapter::JavaScript`, validates the
fetched `runs.using: node24` metadata during admission, and plans it through
the containerized JavaScript executor with lifecycle handling. The fixture
exercises `backend`, `max-size`, and `cache-links`; the other admitted inputs
are recorded with explicit `expected_unsupported` dispositions whose reasons
say they are not selected by this workflow. This keeps the surface schema's
executable-workflow rule intact without claiming the unexercised inputs are
unsupported by Velnor.

## V-3 status

Landed:

- `just refresh-capability-baseline`, the dirty-manifest-source guard, and the
  toolchain isolation that stopped this fixture's pinned toolchain overriding
  the runner's own.
- The sccache microVM correction (F8).

The explicit JavaScript compiler-cache action scenario and surface row are
synchronized with the current manifest. Its workflow uses `backend: github`;
the runner validates the fetched runtime and executes it through the
containerized JavaScript path.

The current baseline is refreshed against the synchronized Velnor commit above,
and the complete local readiness gate passes. No check was removed, skipped, or
loosened to hide stale identity.

## Velnor-side capability surface defects (reported, not edited)

Confirmed against `perf/docker-rust-mbx`. None is fixed here; this repository
does not write to the runner.

1. `crates/velnor-tools/src/main.rs:2375` lists `submodules` among the
   `actions/checkout` inputs `target_audit` treats as supported. The manifest's
   checkout rule set has no `submodules` entry, and `validate_inputs` raises a
   violation for any input with no matching rule, so admission rejects it. The
   audit greenlights a target the runner will refuse.
2. `crates/velnor-tools/src/main.rs:2520` records `actions/setup-python` in
   `expected_target_uses()`, the surface `target_audit` asserts and then prints
   "target audit passed" for. No `actions/setup-python` capability exists in the
   manifest, so that surface is unadmitted. `baptiste0928/cargo-install` and
   `dtolnay/rust-toolchain` in the same list have the same problem.
3. `clean` and `fetch-tags` are admitted by the manifest
   (`InputRule::Literal("clean", …)`, `InputRule::Literal("fetch-tags", …)`) and
   honoured by the checkout implementation (`checkout.rs:136-138`), but are
   absent from that same supported list, so `collect_step` records them as
   unsupported and `target_audit` bails at the `unsupported target workflow
   surface` check. A target using either input is rejected by the audit for
   using something the runner supports.

## Continuation anchor — verifier identity refresh `3d08299`

The fixture baseline and source inventory are now regenerated against the
current shared Velnor branch tip `dfc5777b963fc2494f6939e2b0d631b43b5f606b`.
The capability export remains manifest v12 / crate `0.1.250`, with content
identity
`23749db8aab50310a27021ac24ef7dff7b8480468fd26f800d4b0018b4732229` and source
provenance bound to that exact Velnor commit. The inventory records all six
current Velnor workflow files, including `docs.yml` and the base-owned
`velnor-workflow-policy.yml`, plus their immutable action/runtime pins.

The baseline binding regression now mutates an admitted action subpath,
recomputes a valid content-derived `capability_id`, and proves the audit still
rejects the changed surface. A well-formed forged identity cannot bypass exact
set/row comparison.

Focused proof at this anchor: `just refresh-capability-baseline` and readiness
pass against source `dfc5777`; `python3 .github/scripts/test_audits.py` passes
44 tests; `python3 .github/scripts/audit_capability_coverage.py --contract-only`
passes. No live dual-lane run, deployed image identity, or hosted policy
execution is claimed. The source-side lifecycle, Docker, benchmark, fault/soak,
and mixed post-order gaps remain open under the shared ownership boundaries.

## Continuation anchor — source identity refresh `e5a2792`

The checked-in capability baseline now binds to Velnor source
`ab1cbe1269629389849c45db036ba85c0074ba49` after the benchmark record
validation package. Its manifest v12 / crate `0.1.250` capability identity is
unchanged: `23749db8aab50310a27021ac24ef7dff7b8480468fd26f800d4b0018b4732229`.
The refresh was generated by `just refresh-capability-baseline`; no baseline
field was hand-edited.

Full proof at fixture commit `e5a2792`: `mise run check` passes against that
source (`44` Python tests, `53` Rust tests, workflow/actionlint,
capability-readiness, format/check, and L2 closure). This remains
static/fixture proof. No live dual-lane run, deployed image identity,
default-mbx end-to-end result, VelnorJob benchmark, fault suite, or soak result
is claimed.

## Continuation anchor — Cargo benchmark isolation `d29b0bf`

The source capability baseline now binds to Velnor
`a92074e4a10ab2a53e58c30787db1012120a253d`, whose benchmark driver removes
ambient compiler-wrapper, target, flags, and offline overrides from Cargo
measurements. The manifest v12 / crate `0.1.250` capability identity remains
`23749db8aab50310a27021ac24ef7dff7b8480468fd26f800d4b0018b4732229`.

Full proof at fixture commit `d29b0bf`: `mise run check` passes against that
source (`44` Python tests, `53` Rust tests, workflow/actionlint,
capability-readiness, format/check, and L2 closure). This is still
static/fixture proof; live dual-lane, deployed-image, default-mbx,
VelnorJob-benchmark, fault, and soak results remain unclaimed.

## Continuation anchor — full source gate `a80c430`

The capability baseline now binds to source `2a2b6ae` after the source plan
verification journal was committed. The exported manifest remains v12 / crate
`0.1.250` with capability identity
`23749db8aab50310a27021ac24ef7dff7b8480468fd26f800d4b0018b4732229`.

Full proof at fixture commit `a80c430`: `mise run check` passes against that
exact source (`44` Python tests, `53` Rust tests, workflow/actionlint,
capability-readiness, format/check, and L2 closure). No live dual-lane,
deployed-image, default-mbx, VelnorJob benchmark, fault, or soak result is
claimed.

## Continuation anchor — failed-workload cleanup `d606b2e`

The checked-in capability baseline now binds to Velnor source
`42a392646f12c098e46c407bf6d4e0c74a26737d` after the benchmark workload
runner gained failure-safe teardown. The manifest remains unchanged and the
baseline was regenerated by `just refresh-capability-baseline`.

Full proof at fixture commit `d606b2e`: `mise run check` passes against that
exact source (`44` Python tests, `53` Rust tests, workflow/actionlint,
capability-readiness, format/check, and L2 closure). No live dual-lane,
deployed-image, default-mbx, VelnorJob benchmark, fault, or soak result is
claimed.

## Continuation anchor — cleanup ownership correction `8ebad89`

The checked-in capability baseline now binds to Velnor source
`9b71121b4c5a43fe7942cad6560dd45146849103` after Cargo and Docker benchmark
cleanup became ownership-safe and failure-reporting. The manifest remains
unchanged; the baseline was regenerated by `just refresh-capability-baseline`.

Full proof at fixture commit `8ebad89`: `mise run check` passes against that
exact source (`44` Python tests, `53` Rust tests, workflow/actionlint,
capability-readiness, format/check, and L2 closure). No live dual-lane,
deployed-image, default-mbx, VelnorJob benchmark, fault, or soak result is
claimed.

## Continuation anchor — capability provenance refresh `62fc276`

The supported `VELNOR_SOURCE_DIR=... just refresh-capability-baseline` recipe
was rerun against Velnor
`perf/docker-rust-mbx@c57786af83a65428ca697cf5867abcdc26eb9539`. It exported
manifest v12 / crate `0.1.250`, preserved capability identity
`23749db8aab50310a27021ac24ef7dff7b8480468fd26f800d4b0018b4732229`, and
passed the readiness audit. Only `coverage/velnor-capabilities.json` source
provenance changed; the refresh is committed and pushed at fixture
`62fc276ec4c99524e43fa9c9fa9e40f04a04aef3`. The contract audit, 50 Python
tests, and diff check pass.

`coverage/source-workflow-inventory.md` remains a historical snapshot from
Velnor `dfc5777`; the canonical branch's generated workflow surface changed
after that snapshot. It is not current workflow-parity evidence and requires a
fresh source scan before being used for a readiness claim.
