//! Observation collectors.
//!
//! Every value in an evidence record's `observed` subtree is produced here, by
//! measuring something the job actually did: a process exit status, a file the
//! job wrote, an environment effect a step applied, a GitHub command file, or
//! the step outcomes GitHub itself computed. There is deliberately no
//! collector that stores a value supplied verbatim on the command line — that
//! is the defect this module exists to remove.

use std::collections::BTreeMap;
use std::fs;
use std::path::Path;
use std::process::Command;

use crate::json::{parse, Json};

/// Returns a stable FNV-1a fixture fingerprint of some bytes.
pub fn digest(bytes: &[u8]) -> String {
    let mut hash = 0xcbf2_9ce4_8422_2325_u64;
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x0000_0100_0000_01b3);
    }
    format!("fnv1a64:{hash:016x}")
}

/// Runs a command through `sh -c` and records its observed effect: the exit
/// status and digests of what it wrote.
///
/// # Errors
///
/// Returns an error only when the shell itself cannot be spawned. A failing
/// command is a legitimate observation, not an error.
pub fn command(script: &str) -> Result<Json, String> {
    let output = Command::new("sh")
        .arg("-c")
        .arg(script)
        .output()
        .map_err(|error| format!("failed to run observation {script:?}: {error}"))?;
    let exit_code = match output.status.code() {
        Some(code) => Json::number(u64::from(code.unsigned_abs())),
        None => Json::Null,
    };
    Ok(Json::object([
        ("kind".to_owned(), Json::string("command")),
        ("exit_code".to_owned(), exit_code),
        (
            "signalled".to_owned(),
            Json::Bool(output.status.code().is_none()),
        ),
        (
            "stdout_digest".to_owned(),
            Json::string(digest(&output.stdout)),
        ),
        (
            "stdout_bytes".to_owned(),
            Json::number(output.stdout.len() as u64),
        ),
        (
            "stderr_digest".to_owned(),
            Json::string(digest(&output.stderr)),
        ),
    ]))
}

/// Records what a job produced at `path`: whether it exists, its length and a
/// content digest.
pub fn file(path: &Path) -> Json {
    match fs::read(path) {
        Ok(contents) => Json::object([
            ("kind".to_owned(), Json::string("file")),
            ("present".to_owned(), Json::Bool(true)),
            ("bytes".to_owned(), Json::number(contents.len() as u64)),
            ("digest".to_owned(), Json::string(digest(&contents))),
        ]),
        Err(_) => Json::object([
            ("kind".to_owned(), Json::string("file")),
            ("present".to_owned(), Json::Bool(false)),
        ]),
    }
}

/// Records the environment effect a previous step applied, by reading the
/// variable as it exists now rather than as the workflow claims it should be.
pub fn environment(variable: &str, lookup: &dyn Fn(&str) -> Option<String>) -> Json {
    match lookup(variable) {
        Some(value) => Json::object([
            ("kind".to_owned(), Json::string("environment")),
            ("present".to_owned(), Json::Bool(true)),
            ("digest".to_owned(), Json::string(digest(value.as_bytes()))),
            ("bytes".to_owned(), Json::number(value.len() as u64)),
        ]),
        None => Json::object([
            ("kind".to_owned(), Json::string("environment")),
            ("present".to_owned(), Json::Bool(false)),
        ]),
    }
}

/// Parses a GitHub command file and records the names it set with a digest of
/// each value. Duplicate names are rejected so evidence cannot depend on
/// overwrite order.
///
/// # Errors
///
/// Returns an error when the file cannot be read or is malformed.
pub fn command_file(path: &Path) -> Result<Json, String> {
    let text = fs::read_to_string(path)
        .map_err(|error| format!("failed to read command file {}: {error}", path.display()))?;
    let values = parse_command_file(&text)?;
    Ok(Json::object([
        ("kind".to_owned(), Json::string("command-file")),
        (
            "names".to_owned(),
            Json::Array(values.keys().cloned().map(Json::string).collect()),
        ),
        (
            "values".to_owned(),
            Json::Object(
                values
                    .iter()
                    .map(|(key, value)| (key.clone(), Json::string(digest(value.as_bytes()))))
                    .collect(),
            ),
        ),
    ]))
}

/// Parses GitHub command-file `name=value` and heredoc records.
fn parse_command_file(input: &str) -> Result<BTreeMap<String, String>, String> {
    let lines: Vec<&str> = input.lines().collect();
    let mut values: BTreeMap<String, String> = BTreeMap::new();
    let mut index = 0;
    while index < lines.len() {
        let line = lines[index];
        index += 1;
        if line.is_empty() {
            continue;
        }
        let (name, value) = if let Some((name, delimiter)) = line.split_once("<<") {
            if delimiter.is_empty() || delimiter.chars().any(char::is_whitespace) {
                return Err(format!("line {index}: invalid heredoc delimiter"));
            }
            let start = index;
            while index < lines.len() && lines[index] != delimiter {
                index += 1;
            }
            if index == lines.len() {
                return Err(format!(
                    "line {start}: missing heredoc terminator {delimiter}"
                ));
            }
            let value = lines[start..index].join("\n");
            index += 1;
            (name, value)
        } else {
            let Some((name, value)) = line.split_once('=') else {
                return Err(format!(
                    "line {index}: expected name=value or name<<delimiter"
                ));
            };
            (name, value.to_owned())
        };
        if name.is_empty()
            || !name
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-'))
        {
            return Err(format!("line {index}: invalid command-file name {name:?}"));
        }
        if values.insert(name.to_owned(), value).is_some() {
            return Err(format!(
                "line {index}: duplicate command-file name {name:?}"
            ));
        }
    }
    Ok(values)
}

/// Extracts per-step `outcome` and `conclusion` from a dump of the GitHub
/// `steps` context. These are computed by the runner, not by the workflow, so
/// they are the strongest cross-lane behavioural signal available.
///
/// # Errors
///
/// Returns an error when the dump is unreadable, is not an object, or contains
/// a step entry without both an outcome and a conclusion.
pub fn steps(path: &Path) -> Result<Json, String> {
    let text = fs::read_to_string(path)
        .map_err(|error| format!("failed to read steps context {}: {error}", path.display()))?;
    let value = parse(&text)
        .map_err(|error| format!("invalid steps context {}: {error}", path.display()))?;
    let entries = value
        .as_object()
        .ok_or_else(|| format!("steps context {} must be an object", path.display()))?;
    let mut collected = BTreeMap::new();
    for (step, item) in entries {
        let outcome = item
            .get("outcome")
            .and_then(Json::as_str)
            .ok_or_else(|| format!("step {step:?} has no outcome"))?;
        let conclusion = item
            .get("conclusion")
            .and_then(Json::as_str)
            .ok_or_else(|| format!("step {step:?} has no conclusion"))?;
        collected.insert(
            step.clone(),
            Json::object([
                ("outcome".to_owned(), Json::string(outcome)),
                ("conclusion".to_owned(), Json::string(conclusion)),
            ]),
        );
    }
    if collected.is_empty() {
        return Err(format!(
            "steps context {} recorded no steps; an empty outcome set proves nothing",
            path.display()
        ));
    }
    Ok(Json::object([
        ("kind".to_owned(), Json::string("steps")),
        ("steps".to_owned(), Json::Object(collected)),
    ]))
}

#[cfg(test)]
mod tests {
    use super::{command, command_file, environment, file, steps};
    use crate::json::Json;
    use std::fs;

    fn scratch(name: &str) -> std::path::PathBuf {
        let directory = std::env::temp_dir().join(format!("verifier-observe-{name}"));
        let _ = fs::remove_dir_all(&directory);
        fs::create_dir_all(&directory).expect("scratch directory");
        directory
    }

    #[test]
    fn command_records_a_real_exit_status() {
        let ok = command("printf ok").expect("shell available");
        assert_eq!(ok.get("exit_code"), Some(&Json::number(0)));
        let failed = command("exit 3").expect("shell available");
        assert_eq!(failed.get("exit_code"), Some(&Json::number(3)));
        assert_ne!(ok.get("stdout_digest"), failed.get("stdout_digest"));
    }

    #[test]
    fn file_distinguishes_present_from_absent() {
        let directory = scratch("file");
        let path = directory.join("payload.txt");
        assert_eq!(file(&path).get("present"), Some(&Json::Bool(false)));
        fs::write(&path, b"contents").expect("write payload");
        let present = file(&path);
        assert_eq!(present.get("present"), Some(&Json::Bool(true)));
        assert_eq!(present.get("bytes"), Some(&Json::number(8)));
    }

    #[test]
    fn environment_records_the_effect_not_the_claim() {
        let observed = environment("FIXTURE_EFFECT", &|name| {
            (name == "FIXTURE_EFFECT").then(|| "applied".to_owned())
        });
        assert_eq!(observed.get("present"), Some(&Json::Bool(true)));
        let absent = environment("FIXTURE_EFFECT", &|_| None);
        assert_eq!(absent.get("present"), Some(&Json::Bool(false)));
    }

    #[test]
    fn command_file_rejects_duplicate_names() {
        let directory = scratch("command-file");
        let path = directory.join("env");
        fs::write(&path, "alpha=one\nalpha=two\n").expect("write command file");
        let error = command_file(&path).expect_err("duplicates must fail closed");
        assert!(error.contains("duplicate"), "{error}");
    }

    #[test]
    fn steps_requires_outcomes() {
        let directory = scratch("steps");
        let path = directory.join("steps.json");
        fs::write(
            &path,
            r#"{"build":{"outcome":"success","conclusion":"success"}}"#,
        )
        .expect("write steps");
        let observed = steps(&path).expect("valid steps context");
        assert!(observed.to_json().contains("\"outcome\":\"success\""));

        fs::write(&path, r#"{"build":{"conclusion":"success"}}"#).expect("write steps");
        assert!(steps(&path).is_err());

        fs::write(&path, "{}").expect("write steps");
        assert!(steps(&path).is_err());
    }
}
