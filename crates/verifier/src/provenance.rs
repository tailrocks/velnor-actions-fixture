//! Evidence provenance: the facts a workflow author cannot fabricate.
//!
//! Every provenance field is read from the environment the runner service
//! establishes for the job, never from a command-line argument. A record that
//! cannot be traced to a concrete run, attempt, commit and runner is not
//! evidence, and this module refuses to produce one.

use std::collections::BTreeMap;
use std::time::{SystemTime, UNIX_EPOCH};

use crate::json::Json;

/// Provenance fields that are identical for both lanes of one run and are
/// therefore compared, not normalized away.
pub const COMPARED_FIELDS: &[&str] = &[
    "commit_sha",
    "repository",
    "run_attempt",
    "run_id",
    "run_number",
    "runner_arch",
    "runner_os",
    "workflow",
];

/// Provenance fields that legitimately differ between lanes. This is the whole
/// normalization allowlist: runner identity, the per-lane job identity, the
/// runner's own Velnor build identity and the collection timestamp. Nothing
/// outside this list is ever dropped from a comparison, at any depth.
pub const NORMALIZED_FIELDS: &[&str] = &[
    "collected_at",
    "image_digest",
    "job",
    "lane",
    "runner_environment",
    "runner_name",
    "velnor_manifest_version",
    "velnor_source_sha",
];

/// Every provenance field name, in canonical order.
pub const ALL_FIELDS: &[&str] = &[
    "collected_at",
    "commit_sha",
    "image_digest",
    "job",
    "lane",
    "repository",
    "run_attempt",
    "run_id",
    "run_number",
    "runner_arch",
    "runner_environment",
    "runner_name",
    "runner_os",
    "velnor_manifest_version",
    "velnor_source_sha",
    "workflow",
];

/// Provenance fields that must be present and non-empty in every record.
pub const REQUIRED_FIELDS: &[&str] = &[
    "collected_at",
    "commit_sha",
    "job",
    "lane",
    "repository",
    "run_attempt",
    "run_id",
    "run_number",
    "runner_arch",
    "runner_environment",
    "runner_name",
    "runner_os",
    "workflow",
];

/// The environment variable each required field is collected from.
const SOURCES: &[(&str, &str)] = &[
    ("commit_sha", "GITHUB_SHA"),
    ("job", "GITHUB_JOB"),
    ("repository", "GITHUB_REPOSITORY"),
    ("run_attempt", "GITHUB_RUN_ATTEMPT"),
    ("run_id", "GITHUB_RUN_ID"),
    ("run_number", "GITHUB_RUN_NUMBER"),
    ("runner_arch", "RUNNER_ARCH"),
    ("runner_environment", "RUNNER_ENVIRONMENT"),
    ("runner_name", "RUNNER_NAME"),
    ("runner_os", "RUNNER_OS"),
    ("workflow", "GITHUB_WORKFLOW"),
];

/// Optional provenance collected when the job exposes it.
const OPTIONAL_SOURCES: &[(&str, &str)] = &[
    ("image_digest", "FIXTURE_JOB_IMAGE_DIGEST"),
    ("velnor_manifest_version", "VELNOR_MANIFEST_VERSION"),
    ("velnor_source_sha", "VELNOR_SOURCE_SHA"),
];

fn validate_lane_environment(lane: &str, environment: &str) -> Result<(), String> {
    let expected_lane = match environment {
        "github-hosted" => "github",
        "self-hosted" => "velnor",
        other => {
            return Err(format!(
                "unknown RUNNER_ENVIRONMENT {other:?}; cannot bind evidence to a lane"
            ))
        }
    };
    if expected_lane != lane {
        return Err(format!(
            "lane {lane:?} contradicts RUNNER_ENVIRONMENT {environment:?}, \
             which is lane {expected_lane:?}"
        ));
    }
    Ok(())
}

/// Collected provenance for one evidence record.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Provenance {
    fields: BTreeMap<String, String>,
}

impl Provenance {
    /// Collects provenance from the job environment.
    ///
    /// `lane` names the fixture lane the caller believes it is on; it is
    /// cross-checked against `RUNNER_ENVIRONMENT` so a workflow cannot label a
    /// GitHub-hosted job as a Velnor one or the reverse.
    ///
    /// # Errors
    ///
    /// Returns an error when a required variable is missing or empty, when the
    /// lane contradicts the observed runner environment, or when a numeric
    /// field is not a number.
    pub fn collect(
        lane: &str,
        lookup: &dyn Fn(&str) -> Option<String>,
        now_unix_seconds: u64,
    ) -> Result<Self, String> {
        if lane != "github" && lane != "velnor" {
            return Err(format!("unknown lane {lane:?}"));
        }
        let mut fields = BTreeMap::new();
        for (field, variable) in SOURCES {
            let value = lookup(variable).unwrap_or_default();
            if value.trim().is_empty() {
                return Err(format!(
                    "provenance field {field} is unavailable: {variable} is unset or empty; \
                     evidence can only be collected inside a real job"
                ));
            }
            fields.insert((*field).to_owned(), value);
        }
        for (field, variable) in OPTIONAL_SOURCES {
            if let Some(value) = lookup(variable) {
                if !value.trim().is_empty() {
                    fields.insert((*field).to_owned(), value);
                }
            }
        }

        validate_provenance_identity(&fields)?;
        validate_lane_environment(lane, fields["runner_environment"].as_str())?;
        fields.insert("lane".to_owned(), lane.to_owned());
        fields.insert("collected_at".to_owned(), now_unix_seconds.to_string());
        Ok(Self { fields })
    }

    /// Reads provenance out of a parsed evidence record and checks that it is
    /// complete and well-formed.
    ///
    /// # Errors
    ///
    /// Returns an error when the value is not an object, carries an unknown
    /// field, omits a required one, or carries a lane that contradicts its
    /// runner environment.
    pub fn from_json(value: &Json) -> Result<Self, String> {
        let entries = value
            .as_object()
            .ok_or_else(|| format!("provenance must be an object, found {}", value.type_name()))?;
        let mut fields = BTreeMap::new();
        for (key, item) in entries {
            if !ALL_FIELDS.contains(&key.as_str()) {
                return Err(format!("unknown provenance field {key:?}"));
            }
            let text = item
                .as_str()
                .ok_or_else(|| format!("provenance field {key:?} must be a string"))?;
            fields.insert(key.clone(), text.to_owned());
        }
        for field in REQUIRED_FIELDS {
            match fields.get(*field) {
                Some(value) if !value.trim().is_empty() => {}
                _ => return Err(format!("missing provenance field {field}")),
            }
        }
        validate_provenance_identity(&fields)?;
        validate_lane_environment(
            fields["lane"].as_str(),
            fields["runner_environment"].as_str(),
        )?;
        Ok(Self { fields })
    }

    /// Returns one provenance field.
    pub fn get(&self, field: &str) -> Option<&str> {
        self.fields.get(field).map(String::as_str)
    }

    /// Returns the lane this record was collected on.
    pub fn lane(&self) -> &str {
        self.fields
            .get("lane")
            .map(String::as_str)
            .unwrap_or_default()
    }

    /// Renders provenance as a JSON object.
    pub fn to_json(&self) -> Json {
        Json::Object(
            self.fields
                .iter()
                .map(|(key, value)| (key.clone(), Json::string(value.clone())))
                .collect(),
        )
    }
}

fn validate_provenance_identity(fields: &BTreeMap<String, String>) -> Result<(), String> {
    for field in ["run_id", "run_attempt", "run_number"] {
        let value = fields
            .get(field)
            .ok_or_else(|| format!("missing provenance field {field}"))?;
        if value.parse::<u64>().is_err() {
            return Err(format!(
                "provenance field {field} is not a number: {value:?}"
            ));
        }
    }
    let commit = fields
        .get("commit_sha")
        .ok_or_else(|| "missing provenance field commit_sha".to_owned())?;
    if commit.len() != 40 || !commit.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(format!(
            "provenance field commit_sha is not a full commit SHA: {commit:?}"
        ));
    }
    Ok(())
}

/// Reads the current wall clock as whole seconds since the Unix epoch.
pub fn now_unix_seconds() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|elapsed| elapsed.as_secs())
        .unwrap_or_default()
}

#[cfg(test)]
mod tests {
    use super::{Provenance, ALL_FIELDS, COMPARED_FIELDS, NORMALIZED_FIELDS, REQUIRED_FIELDS};
    use std::collections::BTreeMap;

    fn environment(lane: &str) -> BTreeMap<String, String> {
        let (name, environment) = if lane == "github" {
            ("gh-runner-1", "github-hosted")
        } else {
            ("velnor-mvp-1", "self-hosted")
        };
        [
            ("GITHUB_SHA", "5c8b57aa64dcbfd8fe6b2f6edae625ae344fc496"),
            ("GITHUB_JOB", "suite"),
            ("GITHUB_REPOSITORY", "tailrocks/velnor-actions-fixture"),
            ("GITHUB_RUN_ATTEMPT", "1"),
            ("GITHUB_RUN_ID", "42"),
            ("GITHUB_RUN_NUMBER", "7"),
            ("RUNNER_ARCH", "X64"),
            ("RUNNER_ENVIRONMENT", environment),
            ("RUNNER_NAME", name),
            ("RUNNER_OS", "Linux"),
            ("GITHUB_WORKFLOW", "ci"),
        ]
        .into_iter()
        .map(|(key, value)| (key.to_owned(), value.to_owned()))
        .collect()
    }

    fn collect(lane: &str, variables: &BTreeMap<String, String>) -> Result<Provenance, String> {
        Provenance::collect(lane, &|name| variables.get(name).cloned(), 1_700_000_000)
    }

    #[test]
    fn normalization_allowlist_is_total_and_disjoint() {
        for field in ALL_FIELDS {
            let compared = COMPARED_FIELDS.contains(field);
            let normalized = NORMALIZED_FIELDS.contains(field);
            assert!(
                compared ^ normalized,
                "provenance field {field} must be either compared or normalized, never both or neither"
            );
        }
        assert_eq!(
            ALL_FIELDS.len(),
            COMPARED_FIELDS.len() + NORMALIZED_FIELDS.len()
        );
        for field in REQUIRED_FIELDS {
            assert!(ALL_FIELDS.contains(field));
        }
    }

    #[test]
    fn collects_complete_provenance_inside_a_job() {
        let provenance = collect("velnor", &environment("velnor")).expect("complete environment");
        assert_eq!(provenance.lane(), "velnor");
        assert_eq!(provenance.get("run_id"), Some("42"));
        assert_eq!(provenance.get("collected_at"), Some("1700000000"));
    }

    #[test]
    fn refuses_to_collect_outside_a_job() {
        let mut variables = environment("github");
        variables.remove("GITHUB_RUN_ID");
        let error = collect("github", &variables).expect_err("missing run id must fail");
        assert!(error.contains("GITHUB_RUN_ID"), "{error}");
    }

    #[test]
    fn refuses_a_lane_that_contradicts_the_runner_environment() {
        let error =
            collect("velnor", &environment("github")).expect_err("mislabelled lane must fail");
        assert!(error.contains("contradicts"), "{error}");
    }

    #[test]
    fn refuses_a_truncated_commit() {
        let mut variables = environment("github");
        variables.insert("GITHUB_SHA".to_owned(), "5c8b57a".to_owned());
        let error = collect("github", &variables).expect_err("short SHA must fail");
        assert!(error.contains("commit_sha"), "{error}");
    }
}
