//! The evidence record and the readiness checks applied to it.

use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

use crate::json::{parse, Json};
use crate::provenance::Provenance;

/// Schema identifier for collected evidence. The v1 schema carried authored
/// literals and no provenance; it is not accepted.
pub const SCHEMA: &str = "velnor.fixture.evidence.v2";

/// One evidence record: what was observed, and the run that observed it.
#[derive(Debug, Clone)]
pub struct EvidenceRecord {
    /// Scenario this record belongs to.
    pub scenario: String,
    /// Identifier distinguishing several records of the same scenario and lane.
    pub evidence_id: String,
    /// Collected provenance.
    pub provenance: Provenance,
    /// Observations, keyed by observation name.
    pub observed: BTreeMap<String, Json>,
}

impl EvidenceRecord {
    /// Renders the record as a canonical JSON document with a final newline.
    pub fn to_json_document(&self) -> String {
        let value = Json::object([
            ("schema".to_owned(), Json::string(SCHEMA)),
            ("scenario".to_owned(), Json::string(self.scenario.clone())),
            (
                "evidence_id".to_owned(),
                Json::string(self.evidence_id.clone()),
            ),
            ("provenance".to_owned(), self.provenance.to_json()),
            (
                "observed".to_owned(),
                Json::Object(self.observed.clone().into_iter().collect()),
            ),
        ]);
        let mut document = value.to_json();
        document.push('\n');
        document
    }

    /// Parses a record, rejecting anything that is not schema v2 with complete
    /// provenance and a non-empty observation set.
    ///
    /// # Errors
    ///
    /// Returns a message naming the first structural defect found.
    pub fn parse_record(text: &str) -> Result<Self, String> {
        let value = parse(text).map_err(|error| format!("invalid evidence JSON: {error}"))?;
        let entries = value
            .as_object()
            .ok_or_else(|| "evidence root must be an object".to_owned())?;

        let schema = entries
            .get("schema")
            .and_then(Json::as_str)
            .ok_or_else(|| "evidence has no schema".to_owned())?;
        if schema != SCHEMA {
            return Err(format!(
                "unsupported evidence schema {schema:?}; expected {SCHEMA:?}. \
                 Records without collected provenance are not evidence."
            ));
        }
        let scenario = required_string(entries, "scenario")?;
        let evidence_id = required_string(entries, "evidence_id")?;
        let provenance = Provenance::from_json(
            entries
                .get("provenance")
                .ok_or_else(|| "evidence has no provenance".to_owned())?,
        )?;
        let observed = entries
            .get("observed")
            .and_then(Json::as_object)
            .ok_or_else(|| "evidence has no observed object".to_owned())?;
        if observed.is_empty() {
            return Err("evidence records no observations".to_owned());
        }
        Ok(Self {
            scenario,
            evidence_id,
            provenance,
            observed: observed.clone(),
        })
    }

    /// Loads a record from disk.
    ///
    /// # Errors
    ///
    /// Returns an error when the file cannot be read or is not a valid record.
    pub fn load(path: &Path) -> Result<Self, String> {
        let text = fs::read_to_string(path)
            .map_err(|error| format!("failed to read evidence {}: {error}", path.display()))?;
        Self::parse_record(&text).map_err(|error| format!("{}: {error}", path.display()))
    }
}

fn required_string(entries: &BTreeMap<String, Json>, key: &str) -> Result<String, String> {
    let value = entries
        .get(key)
        .and_then(Json::as_str)
        .ok_or_else(|| format!("evidence field {key} must be a non-empty string"))?;
    if value.trim().is_empty() {
        return Err(format!("evidence field {key} must be a non-empty string"));
    }
    Ok(value.to_owned())
}

/// The run an evidence set must belong to for readiness to be established.
#[derive(Debug, Clone, Default)]
pub struct Expectation {
    /// The run id currently being verified.
    pub run_id: Option<String>,
    /// The run attempt currently being verified.
    pub run_attempt: Option<String>,
    /// The fixture commit under test.
    pub commit_sha: Option<String>,
    /// The Velnor source commit under test, required of Velnor-lane records.
    pub velnor_source_sha: Option<String>,
    /// The Velnor manifest version under test, required of Velnor-lane records.
    pub velnor_manifest_version: Option<String>,
}

impl Expectation {
    /// Checks one record against the run under test.
    ///
    /// # Errors
    ///
    /// Returns every mismatch found, so a caller sees the whole picture rather
    /// than the first problem.
    pub fn check(&self, record: &EvidenceRecord) -> Vec<String> {
        let mut failures = Vec::new();
        let label = format!("{}/{}", record.scenario, record.evidence_id);
        let mut compare = |field: &str, expected: &Option<String>| {
            if let Some(expected) = expected {
                let actual = record.provenance.get(field).unwrap_or_default();
                if actual != expected {
                    failures.push(format!(
                        "{label} ({}): {field} is {actual:?}, expected {expected:?}",
                        record.provenance.lane()
                    ));
                }
            }
        };
        compare("run_id", &self.run_id);
        compare("run_attempt", &self.run_attempt);
        compare("commit_sha", &self.commit_sha);

        if record.provenance.lane() == "velnor" {
            for (field, expected) in [
                ("velnor_source_sha", &self.velnor_source_sha),
                ("velnor_manifest_version", &self.velnor_manifest_version),
            ] {
                let Some(expected) = expected else { continue };
                match record.provenance.get(field) {
                    None => failures.push(format!(
                        "{label} (velnor): {field} is absent; the record does not identify the \
                         Velnor build that produced it"
                    )),
                    Some(actual) if actual != expected => failures.push(format!(
                        "{label} (velnor): {field} is {actual:?}, expected {expected:?}; \
                         this evidence was produced against a different Velnor build"
                    )),
                    Some(_) => {}
                }
            }
        }
        failures
    }
}

/// An indexed evidence set: one record per lane per evidence id.
#[derive(Debug)]
pub struct EvidenceSet {
    records: BTreeMap<(String, String), (PathBuf, EvidenceRecord)>,
}

impl EvidenceSet {
    /// Loads every `*.json` file under `directory` as an evidence record for
    /// `scenario`.
    ///
    /// # Errors
    ///
    /// Returns an error when a file is not a valid record, belongs to another
    /// scenario, or duplicates an existing (lane, evidence id) pair.
    pub fn load(directory: &Path, scenario: &str) -> Result<Self, String> {
        let mut paths = Vec::new();
        collect_json(directory, &mut paths)?;
        paths.sort();
        let mut records = BTreeMap::new();
        for path in paths {
            let record = EvidenceRecord::load(&path)?;
            if record.scenario != scenario {
                return Err(format!(
                    "{}: scenario is {:?}, expected {scenario:?}",
                    path.display(),
                    record.scenario
                ));
            }
            let key = (
                record.provenance.lane().to_owned(),
                record.evidence_id.clone(),
            );
            if let Some((existing, _)) = records.get(&key) {
                return Err(format!(
                    "duplicate evidence for lane {} id {}: {} and {}",
                    key.0,
                    key.1,
                    PathBuf::from(existing).display(),
                    path.display()
                ));
            }
            records.insert(key, (path, record));
        }
        if records.is_empty() {
            return Err(format!("no evidence found in {}", directory.display()));
        }
        Ok(Self { records })
    }

    /// The lanes represented in this set.
    pub fn lanes(&self) -> Vec<String> {
        let mut lanes: Vec<String> = self.records.keys().map(|(lane, _)| lane.clone()).collect();
        lanes.sort();
        lanes.dedup();
        lanes
    }

    /// The evidence ids represented in this set.
    pub fn evidence_ids(&self) -> Vec<String> {
        let mut ids: Vec<String> = self.records.keys().map(|(_, id)| id.clone()).collect();
        ids.sort();
        ids.dedup();
        ids
    }

    /// Looks up one record.
    pub fn get(&self, lane: &str, evidence_id: &str) -> Option<&EvidenceRecord> {
        self.records
            .get(&(lane.to_owned(), evidence_id.to_owned()))
            .map(|(_, record)| record)
    }

    /// Every record in the set.
    pub fn records(&self) -> impl Iterator<Item = &EvidenceRecord> {
        self.records.values().map(|(_, record)| record)
    }
}

fn collect_json(directory: &Path, paths: &mut Vec<PathBuf>) -> Result<(), String> {
    let entries = fs::read_dir(directory)
        .map_err(|error| format!("failed to read {}: {error}", directory.display()))?;
    for entry in entries {
        let entry =
            entry.map_err(|error| format!("failed to read {}: {error}", directory.display()))?;
        let path = entry.path();
        if path.is_dir() {
            collect_json(&path, paths)?;
        } else if path.extension().and_then(|value| value.to_str()) == Some("json") {
            paths.push(path);
        }
    }
    Ok(())
}
