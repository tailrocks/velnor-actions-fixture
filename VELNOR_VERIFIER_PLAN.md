# Velnor readiness verifier — oracle repair plan (V-1)

## Starting state

| Tree | Branch | Commit |
| --- | --- | --- |
| `velnor-actions-fixture` (this repository) | `codex/verifier-completion-fixes` | `5c8b57aa64dcbfd8fe6b2f6edae625ae344fc496` |
| `velnor` (runner under test) | `perf/docker-rust-mbx` | `2858e92df0eb78df4f1a6fe2ad4cbf86f1d56355` |

`crates/velnor-runner/src/manifest.rs` is byte-identical between
`2858e92d` and the current tip of `perf/docker-rust-mbx`, so the manifest
identity recorded below is the identity of the runner under test.

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

### F3 — the capability baseline is stale and cannot detect it (verified)

`audit_capability_coverage.py:25-26` pins `EXPECTED_MANIFEST_VERSION = 10` and
`EXPECTED_SOURCE_SHA = 2fad3ffbd3f813f1b504de14163f9b57799b5e8c`;
`coverage/velnor-capabilities.json:2-3` agrees. The runner under test is
manifest **v11** (`crates/velnor-runner/src/manifest.rs:18`).
`crate_version` is `0.1.250` on both sides
(`crates/velnor-runner/Cargo.toml:3`), so the version pin gives a false
all-clear. `validate_manifest`
(`audit_capability_coverage.py:167-232`) compares the checked-in JSON against
Python constants; it never reads Velnor.

### F4 — cardinality cannot detect identity drift (verified)

`kunobi-ninja/kache-action` no longer exists in the runner manifest — the only
surviving mention at `2858e92d` is the changelog comment on
`crates/velnor-runner/src/manifest.rs:17`. The runner admits
`jdx/mr-boxington-action` in its place. Both sides hold exactly 30 admitted
action repositories, so `EXPECTED_ACTION_COUNT = 30`
(`audit_capability_coverage.py:27`) passed straight through a breaking change:

```
only in fixture baseline: kunobi-ninja/kache-action
only in runner manifest:  jdx/mr-boxington-action
```

`compat.yml:239-260` still runs the removed action and
`audit_capability_coverage.py:666-693` still enforces it as a hard contract
(`EXPECTED_KACHE_REF`, `EXPECTED_KACHE_VERSION`).

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
- The Kache contract is removed together with the `compat.yml` step that
  exercises it, because the runner no longer admits that identity.

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
| V-1.b1 | Delete `EXPECTED_MANIFEST_VERSION`, `EXPECTED_SOURCE_SHA`, `EXPECTED_ACTION_COUNT`, `EXPECTED_REUSABLE_WORKFLOW_COUNT`; bind the baseline to a live export or runner source | Audit fails loudly against a v10 baseline and passes against a v11 one derived from the runner |
| V-1.b2 | Replace cardinality with set identity for actions and reusable workflows | Swapping one repository for another in either document fails the audit |
| V-1.b3 | Remove the Kache contract and its `compat.yml` step; refresh the baseline to v11 identity | No `kache` reference remains in scripts, coverage or workflows |
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

## Out of scope for V-1

The Rust scenario matrix (`sccache` versus `mr-boxington`) is untouched. It is
a separate package of work; this task only removes the false all-clear that
hid the manifest change which introduced it.
