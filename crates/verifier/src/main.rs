//! `verifier` — collect, verify and compare Velnor readiness evidence.
//!
//! ```text
//! verifier collect --scenario S --evidence-id ID --lane github|velnor --output PATH
//!                  [--observe-command NAME=SCRIPT] [--observe-file NAME=PATH]
//!                  [--observe-env NAME=VARIABLE] [--observe-command-file NAME=PATH]
//!                  [--observe-steps NAME=PATH]
//! verifier verify  --directory DIR --scenario S [--expect-run-id ID]
//!                  [--expect-run-attempt N] [--expect-commit SHA]
//!                  [--expect-velnor-source-sha SHA]
//!                  [--expect-velnor-manifest-version N]
//! verifier compare --directory DIR --scenario S --lanes github velnor [verify options]
//! ```

use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

use verifier::compare::compare;
use verifier::json::Json;
use verifier::observe;
use verifier::provenance::{now_unix_seconds, Provenance};
use verifier::record::{EvidenceRecord, EvidenceSet, Expectation};

fn main() -> ExitCode {
    let arguments: Vec<String> = env::args().skip(1).collect();
    match run(&arguments) {
        Ok(message) => {
            println!("{message}");
            ExitCode::SUCCESS
        }
        Err(failures) => {
            for failure in &failures {
                eprintln!("ERROR: {failure}");
            }
            eprintln!("verifier failed: {} error(s)", failures.len());
            ExitCode::from(1)
        }
    }
}

fn run(arguments: &[String]) -> Result<String, Vec<String>> {
    let Some((command, rest)) = arguments.split_first() else {
        return Err(vec![
            "usage: verifier <collect|verify|compare> ...".to_owned()
        ]);
    };
    let options = Options::parse(rest).map_err(|error| vec![error])?;
    match command.as_str() {
        "collect" => collect(&options).map_err(|error| vec![error]),
        "verify" => verify(&options).map(|(message, _)| message),
        "compare" => compare_lanes(&options),
        other => Err(vec![format!("unknown command {other:?}")]),
    }
}

#[derive(Default)]
struct Options {
    scenario: Option<String>,
    evidence_id: Option<String>,
    lane: Option<String>,
    output: Option<PathBuf>,
    directory: Option<PathBuf>,
    lanes: Vec<String>,
    expect_run_id: Option<String>,
    expect_run_attempt: Option<String>,
    expect_commit: Option<String>,
    expect_velnor_source_sha: Option<String>,
    expect_velnor_manifest_version: Option<String>,
    observations: Vec<(String, Observation)>,
}

enum Observation {
    Command(String),
    File(PathBuf),
    Environment(String),
    CommandFile(PathBuf),
    Steps(PathBuf),
}

impl Options {
    fn parse(arguments: &[String]) -> Result<Self, String> {
        let mut options = Self::default();
        let mut index = 0;
        while index < arguments.len() {
            let flag = arguments[index].as_str();
            let mut value = || -> Result<String, String> {
                index += 1;
                arguments
                    .get(index)
                    .cloned()
                    .ok_or_else(|| format!("missing value for {flag}"))
            };
            match flag {
                "--scenario" => options.scenario = Some(value()?),
                "--evidence-id" => options.evidence_id = Some(value()?),
                "--lane" => options.lane = Some(value()?),
                "--output" => options.output = Some(PathBuf::from(value()?)),
                "--directory" => options.directory = Some(PathBuf::from(value()?)),
                "--expect-run-id" => options.expect_run_id = Some(value()?),
                "--expect-run-attempt" => options.expect_run_attempt = Some(value()?),
                "--expect-commit" => options.expect_commit = Some(value()?),
                "--expect-velnor-source-sha" => {
                    options.expect_velnor_source_sha = Some(value()?);
                }
                "--expect-velnor-manifest-version" => {
                    options.expect_velnor_manifest_version = Some(value()?);
                }
                "--lanes" => {
                    index += 1;
                    while let Some(lane) = arguments.get(index) {
                        if lane.starts_with("--") {
                            break;
                        }
                        options.lanes.push(lane.clone());
                        index += 1;
                    }
                    continue;
                }
                "--observe-command"
                | "--observe-file"
                | "--observe-env"
                | "--observe-command-file"
                | "--observe-steps" => {
                    let raw = value()?;
                    let (name, argument) = raw
                        .split_once('=')
                        .ok_or_else(|| format!("{flag} expects NAME=VALUE, got {raw:?}"))?;
                    if name.is_empty() {
                        return Err(format!("{flag} expects a non-empty observation name"));
                    }
                    let observation = match flag {
                        "--observe-command" => Observation::Command(argument.to_owned()),
                        "--observe-file" => Observation::File(PathBuf::from(argument)),
                        "--observe-env" => Observation::Environment(argument.to_owned()),
                        "--observe-command-file" => {
                            Observation::CommandFile(PathBuf::from(argument))
                        }
                        _ => Observation::Steps(PathBuf::from(argument)),
                    };
                    options.observations.push((name.to_owned(), observation));
                }
                other => return Err(format!("unknown argument {other:?}")),
            }
            index += 1;
        }
        Ok(options)
    }

    fn expectation(&self) -> Expectation {
        Expectation {
            run_id: self.expect_run_id.clone(),
            run_attempt: self.expect_run_attempt.clone(),
            commit_sha: self.expect_commit.clone(),
            velnor_source_sha: self.expect_velnor_source_sha.clone(),
            velnor_manifest_version: self.expect_velnor_manifest_version.clone(),
        }
    }

    fn require<'a, T>(&self, value: &'a Option<T>, flag: &str) -> Result<&'a T, String> {
        value.as_ref().ok_or_else(|| format!("missing {flag}"))
    }
}

fn collect(options: &Options) -> Result<String, String> {
    let scenario = options.require(&options.scenario, "--scenario")?;
    let evidence_id = options.require(&options.evidence_id, "--evidence-id")?;
    let lane = options.require(&options.lane, "--lane")?;
    let output = options.require(&options.output, "--output")?;
    if options.observations.is_empty() {
        return Err(
            "collect requires at least one observation; a record with no observations \
             proves nothing"
                .to_owned(),
        );
    }

    let provenance = Provenance::collect(lane, &|name| env::var(name).ok(), now_unix_seconds())?;
    let mut observed: BTreeMap<String, Json> = BTreeMap::new();
    for (name, observation) in &options.observations {
        let value = match observation {
            Observation::Command(script) => observe::command(script)?,
            Observation::File(path) => observe::file(path),
            Observation::Environment(variable) => {
                observe::environment(variable, &|name| env::var(name).ok())
            }
            Observation::CommandFile(path) => observe::command_file(path)?,
            Observation::Steps(path) => observe::steps(path)?,
        };
        if observed.insert(name.clone(), value).is_some() {
            return Err(format!("duplicate observation name {name:?}"));
        }
    }

    let record = EvidenceRecord {
        scenario: scenario.clone(),
        evidence_id: evidence_id.clone(),
        provenance,
        observed,
    };
    if let Some(parent) = output.parent() {
        if !parent.as_os_str().is_empty() {
            fs::create_dir_all(parent)
                .map_err(|error| format!("failed to create {}: {error}", parent.display()))?;
        }
    }
    fs::write(output, record.to_json_document())
        .map_err(|error| format!("failed to write {}: {error}", output.display()))?;
    Ok(format!(
        "collected {} observation(s) for {scenario}/{evidence_id} on lane {lane} -> {}",
        options.observations.len(),
        output.display()
    ))
}

fn verify(options: &Options) -> Result<(String, EvidenceSet), Vec<String>> {
    let scenario = options
        .require(&options.scenario, "--scenario")
        .map_err(|error| vec![error])?;
    let directory: &Path = options
        .require(&options.directory, "--directory")
        .map_err(|error| vec![error])?;
    let set = EvidenceSet::load(directory, scenario).map_err(|error| vec![error])?;
    let expectation = options.expectation();
    let mut failures = Vec::new();
    let mut count = 0;
    for record in set.records() {
        failures.extend(expectation.check(record));
        count += 1;
    }
    if failures.is_empty() {
        Ok((
            format!("{count} evidence record(s) carry provenance for the run under test"),
            set,
        ))
    } else {
        Err(failures)
    }
}

fn compare_lanes(options: &Options) -> Result<String, Vec<String>> {
    let (verified, set) = verify(options)?;
    let lanes = if options.lanes.is_empty() {
        return Err(vec!["missing --lanes".to_owned()]);
    } else {
        options.lanes.clone()
    };
    let compared = compare(&set, &lanes)?;
    Ok(format!("{verified}\n{compared}"))
}
