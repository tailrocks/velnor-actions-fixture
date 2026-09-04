//! Mutation tests: proof that the oracle can fail.
//!
//! The verifier's previous incarnation could not fail on behaviour, and the
//! reason nobody noticed is that nothing ever fed it wrong evidence. Each test
//! here starts from an evidence set that must pass, mutates exactly one thing
//! a broken runner or a dishonest workflow would change, and asserts the
//! verifier rejects it with a message naming the defect.
//!
//! A test that only proved acceptance would be worthless: the bug class was
//! "always accepts". Every case below is a rejection case.

use std::fs;
use std::path::{Path, PathBuf};

use verifier::compare::compare;
use verifier::record::{EvidenceRecord, EvidenceSet, Expectation};

const RUN_ID: &str = "9001";
const RUN_ATTEMPT: &str = "1";
const COMMIT: &str = "5c8b57aa64dcbfd8fe6b2f6edae625ae344fc496";
const VELNOR_SHA: &str = "dd939638ac9398b9b414463814a1ee9b6526989f";
const MANIFEST_VERSION: &str = "11";

/// Builds a well-formed record for one lane. `observed` is injected verbatim so
/// individual tests can diverge exactly one observation.
fn record(lane: &str, observed: &str) -> String {
    let (runner_name, environment) = if lane == "github" {
        ("gh-hosted-7", "github-hosted")
    } else {
        ("velnor-target-mvp-3", "self-hosted")
    };
    let velnor = if lane == "velnor" {
        format!(
            r#","velnor_manifest_version":"{MANIFEST_VERSION}","velnor_source_sha":"{VELNOR_SHA}""#
        )
    } else {
        String::new()
    };
    format!(
        r#"{{"schema":"velnor.fixture.evidence.v2","scenario":"rust","evidence_id":"suite",
        "provenance":{{"collected_at":"1700000000","commit_sha":"{COMMIT}","job":"rust-{lane}",
        "lane":"{lane}","repository":"tailrocks/velnor-actions-fixture",
        "run_attempt":"{RUN_ATTEMPT}","run_id":"{RUN_ID}","run_number":"12",
        "runner_arch":"X64","runner_environment":"{environment}","runner_name":"{runner_name}",
        "runner_os":"Linux","workflow":"ci"{velnor}}},
        "observed":{observed}}}"#
    )
}

const HEALTHY_OBSERVED: &str = r#"{"nextest":{"kind":"command","exit_code":0,"signalled":false,
    "stdout_digest":"fnv1a64:0000000000000001","stdout_bytes":11,
    "stderr_digest":"fnv1a64:0000000000000002"},
    "steps":{"kind":"steps","steps":{"build":{"outcome":"success","conclusion":"success"}}}}"#;

fn scratch(name: &str) -> PathBuf {
    let directory = std::env::temp_dir().join(format!("verifier-mutation-{name}"));
    let _ = fs::remove_dir_all(&directory);
    fs::create_dir_all(&directory).expect("scratch directory");
    directory
}

fn write(directory: &Path, lane: &str, body: &str) {
    fs::write(directory.join(format!("{lane}.json")), body).expect("write evidence");
}

fn expectation() -> Expectation {
    Expectation {
        run_id: Some(RUN_ID.to_owned()),
        run_attempt: Some(RUN_ATTEMPT.to_owned()),
        commit_sha: Some(COMMIT.to_owned()),
        velnor_source_sha: Some(VELNOR_SHA.to_owned()),
        velnor_manifest_version: Some(MANIFEST_VERSION.to_owned()),
    }
}

fn lanes() -> Vec<String> {
    vec!["github".to_owned(), "velnor".to_owned()]
}

fn check(directory: &Path) -> Result<String, Vec<String>> {
    let set = EvidenceSet::load(directory, "rust").map_err(|error| vec![error])?;
    let expectation = expectation();
    let mut failures: Vec<String> = set
        .records()
        .flat_map(|record| expectation.check(record))
        .collect();
    if !failures.is_empty() {
        failures.sort();
        return Err(failures);
    }
    compare(&set, &lanes())
}

fn rejection(directory: &Path) -> String {
    match check(directory) {
        Ok(message) => panic!("the verifier accepted mutated evidence: {message}"),
        Err(failures) => failures.join(" | "),
    }
}

/// Control: an honest, agreeing dual-lane evidence set is accepted. Without
/// this the rejection tests could pass for the wrong reason.
#[test]
fn honest_dual_lane_evidence_is_accepted() {
    let directory = scratch("control");
    write(&directory, "github", &record("github", HEALTHY_OBSERVED));
    write(&directory, "velnor", &record("velnor", HEALTHY_OBSERVED));
    let message = check(&directory).expect("honest evidence must pass");
    assert!(message.contains("match across lanes"), "{message}");
}

/// Stale evidence: a record produced by an earlier run of the same workflow.
#[test]
fn stale_evidence_from_a_previous_run_is_rejected() {
    let directory = scratch("stale");
    write(&directory, "github", &record("github", HEALTHY_OBSERVED));
    write(
        &directory,
        "velnor",
        &record("velnor", HEALTHY_OBSERVED)
            .replace(&format!(r#""run_id":"{RUN_ID}""#), r#""run_id":"8000""#),
    );
    let failure = rejection(&directory);
    assert!(failure.contains("run_id"), "{failure}");
}

/// A re-run of the same run id under a different attempt is equally stale.
#[test]
fn evidence_from_a_previous_run_attempt_is_rejected() {
    let directory = scratch("attempt");
    write(&directory, "github", &record("github", HEALTHY_OBSERVED));
    write(
        &directory,
        "velnor",
        &record("velnor", HEALTHY_OBSERVED).replace(r#""run_attempt":"1""#, r#""run_attempt":"3""#),
    );
    let failure = rejection(&directory);
    assert!(failure.contains("run_attempt"), "{failure}");
}

/// Evidence collected against a different fixture commit.
#[test]
fn evidence_for_a_different_fixture_commit_is_rejected() {
    let directory = scratch("commit");
    write(&directory, "github", &record("github", HEALTHY_OBSERVED));
    write(
        &directory,
        "velnor",
        &record("velnor", HEALTHY_OBSERVED)
            .replace(COMMIT, "0000000000000000000000000000000000000000"),
    );
    let failure = rejection(&directory);
    assert!(failure.contains("commit_sha"), "{failure}");
}

/// Evidence produced against a different Velnor build. This is the mutation
/// that the old audit could never detect: identical fixture inputs, different
/// runner under the hood.
#[test]
fn evidence_from_a_different_velnor_build_is_rejected() {
    let directory = scratch("velnor-build");
    write(&directory, "github", &record("github", HEALTHY_OBSERVED));
    write(
        &directory,
        "velnor",
        &record("velnor", HEALTHY_OBSERVED)
            .replace(VELNOR_SHA, "2fad3ffbd3f813f1b504de14163f9b57799b5e8c"),
    );
    let failure = rejection(&directory);
    assert!(failure.contains("different Velnor build"), "{failure}");
}

/// A Velnor-lane record that simply omits its Velnor identity.
#[test]
fn velnor_evidence_without_a_build_identity_is_rejected() {
    let directory = scratch("velnor-anonymous");
    write(&directory, "github", &record("github", HEALTHY_OBSERVED));
    let anonymous = record("velnor", HEALTHY_OBSERVED)
        .replace(&format!(r#","velnor_source_sha":"{VELNOR_SHA}""#), "");
    write(&directory, "velnor", &anonymous);
    let failure = rejection(&directory);
    assert!(failure.contains("velnor_source_sha"), "{failure}");
}

/// A missing lane must fail, not pass quietly.
#[test]
fn a_missing_lane_is_rejected() {
    let directory = scratch("missing-lane");
    write(&directory, "github", &record("github", HEALTHY_OBSERVED));
    let failure = rejection(&directory);
    assert!(
        failure.contains("missing evidence for lane velnor"),
        "{failure}"
    );
}

/// A single-lane comparison must be an error, not a silent success. The old
/// comparator printed "parity not claimed" and returned zero.
#[test]
fn a_single_lane_comparison_is_an_error() {
    let directory = scratch("single-lane");
    write(&directory, "velnor", &record("velnor", HEALTHY_OBSERVED));
    let set = EvidenceSet::load(&directory, "rust").expect("valid evidence");
    let failures =
        compare(&set, &["velnor".to_owned()]).expect_err("a single lane cannot establish parity");
    assert!(
        failures.join(" ").contains("at least two lanes"),
        "{failures:?}"
    );
}

/// The behavioural case: the Velnor lane observed a different exit code.
#[test]
fn a_divergent_exit_code_is_rejected() {
    let directory = scratch("exit-code");
    write(&directory, "github", &record("github", HEALTHY_OBSERVED));
    write(
        &directory,
        "velnor",
        &record(
            "velnor",
            &HEALTHY_OBSERVED.replace(r#""exit_code":0"#, r#""exit_code":101"#),
        ),
    );
    let failure = rejection(&directory);
    assert!(
        failure.contains("observed.nextest.exit_code differs"),
        "{failure}"
    );
}

/// The behavioural case GitHub itself computes: a step concluded differently.
#[test]
fn a_divergent_step_conclusion_is_rejected() {
    let directory = scratch("step-conclusion");
    write(&directory, "github", &record("github", HEALTHY_OBSERVED));
    write(
        &directory,
        "velnor",
        &record(
            "velnor",
            &HEALTHY_OBSERVED.replace(r#""conclusion":"success""#, r#""conclusion":"failure""#),
        ),
    );
    let failure = rejection(&directory);
    assert!(
        failure.contains("observed.steps.steps.build.conclusion differs"),
        "{failure}"
    );
}

/// Divergence nested under a key named `runner`. The old comparators dropped
/// any subtree with that key at any depth, so this mutation was invisible.
#[test]
fn divergence_nested_under_a_key_named_runner_is_rejected() {
    let directory = scratch("runner-subtree");
    let observed = r#"{"probe":{"kind":"command","runner":{"exit_code":0},"lane":{"bytes":3}}}"#;
    write(&directory, "github", &record("github", observed));
    write(
        &directory,
        "velnor",
        &record(
            "velnor",
            &observed.replace(r#""exit_code":0"#, r#""exit_code":7"#),
        ),
    );
    let failure = rejection(&directory);
    assert!(
        failure.contains("observed.probe.runner.exit_code differs"),
        "{failure}"
    );
}

/// Provenance cannot simply be omitted.
#[test]
fn evidence_without_provenance_is_rejected() {
    let directory = scratch("no-provenance");
    write(&directory, "github", &record("github", HEALTHY_OBSERVED));
    fs::write(
        directory.join("velnor.json"),
        r#"{"schema":"velnor.fixture.evidence.v2","scenario":"rust","evidence_id":"suite",
        "observed":{"nextest":{"exit_code":0}}}"#,
    )
    .expect("write evidence");
    let failure = rejection(&directory);
    assert!(failure.contains("no provenance"), "{failure}");
}

/// Partly fabricated provenance: the fields a workflow author could plausibly
/// invent are present, but the ones the runner supplies are missing.
#[test]
fn fabricated_partial_provenance_is_rejected() {
    let directory = scratch("fabricated");
    write(&directory, "github", &record("github", HEALTHY_OBSERVED));
    fs::write(
        directory.join("velnor.json"),
        format!(
            r#"{{"schema":"velnor.fixture.evidence.v2","scenario":"rust","evidence_id":"suite",
            "provenance":{{"lane":"velnor","run_id":"{RUN_ID}","commit_sha":"{COMMIT}"}},
            "observed":{HEALTHY_OBSERVED}}}"#
        ),
    )
    .expect("write evidence");
    let failure = rejection(&directory);
    assert!(failure.contains("missing provenance field"), "{failure}");
}

/// Provenance carrying an invented field is rejected rather than ignored, so a
/// workflow cannot smuggle an authored value into the record.
#[test]
fn invented_provenance_fields_are_rejected() {
    let directory = scratch("invented-field");
    write(&directory, "github", &record("github", HEALTHY_OBSERVED));
    write(
        &directory,
        "velnor",
        &record("velnor", HEALTHY_OBSERVED)
            .replace(r#""workflow":"ci""#, r#""workflow":"ci","verdict":"pass""#),
    );
    let failure = rejection(&directory);
    assert!(failure.contains("unknown provenance field"), "{failure}");
}

/// The pre-repair schema, whose records carried authored literals and no
/// provenance at all, is not accepted as evidence.
#[test]
fn the_pre_repair_evidence_schema_is_rejected() {
    let legacy = r#"{"schema":"velnor.fixture.evidence.v1","scenario":"rust","lane":"velnor",
        "build":"fixture-harness-build-v1","fields":{"result":"pass"}}"#;
    let error = EvidenceRecord::parse_record(legacy).expect_err("v1 records are not evidence");
    assert!(error.contains("velnor.fixture.evidence.v2"), "{error}");
}

/// Two records claiming the same lane and evidence id cannot both be counted.
#[test]
fn duplicate_lane_evidence_is_rejected() {
    let directory = scratch("duplicate");
    write(&directory, "github", &record("github", HEALTHY_OBSERVED));
    write(&directory, "velnor", &record("velnor", HEALTHY_OBSERVED));
    fs::write(
        directory.join("velnor-copy.json"),
        record("velnor", HEALTHY_OBSERVED),
    )
    .expect("write evidence");
    let failure = rejection(&directory);
    assert!(failure.contains("duplicate evidence"), "{failure}");
}

/// A record with no observations proves nothing and is not evidence.
#[test]
fn evidence_without_observations_is_rejected() {
    let error = EvidenceRecord::parse_record(&record("github", "{}"))
        .expect_err("an empty observation set is not evidence");
    assert!(error.contains("no observations"), "{error}");
}
