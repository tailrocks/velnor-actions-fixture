//! Cross-lane comparison.
//!
//! Two rules define this module.
//!
//! 1. The `observed` subtree is compared verbatim at every depth. Nothing in it
//!    is ever normalized away, whatever a key happens to be named.
//! 2. Provenance is split by an explicit, closed, typed allowlist: the fields
//!    in [`NORMALIZED_FIELDS`] may differ between lanes; every other provenance
//!    field must be equal. A unit test proves the split is total and disjoint,
//!    so a new provenance field cannot silently join the normalized set.
//!
//! A single-lane comparison is an error. One lane cannot establish parity, and
//! reporting success for it is how a verifier stops being an oracle.

use crate::json::Json;
use crate::provenance::{COMPARED_FIELDS, NORMALIZED_FIELDS};
use crate::record::EvidenceSet;

/// Compares every evidence id across every requested lane.
///
/// # Errors
///
/// Returns every difference found: missing lanes, missing records, divergent
/// provenance outside the normalization allowlist, and divergent observations.
pub fn compare(set: &EvidenceSet, lanes: &[String]) -> Result<String, Vec<String>> {
    if lanes.len() < 2 {
        return Err(vec![format!(
            "cross-lane comparison requires at least two lanes, got {:?}; a single-lane \
             dispatch is diagnostic and cannot establish parity",
            lanes
        )]);
    }
    let mut failures = Vec::new();
    let observed_lanes = set.lanes();
    for lane in lanes {
        if !observed_lanes.contains(lane) {
            failures.push(format!("missing evidence for lane {lane}"));
        }
    }
    for lane in &observed_lanes {
        if !lanes.contains(lane) {
            failures.push(format!("unexpected evidence for lane {lane}"));
        }
    }
    if !failures.is_empty() {
        return Err(failures);
    }

    let evidence_ids = set.evidence_ids();
    let baseline_lane = &lanes[0];
    for evidence_id in &evidence_ids {
        let Some(baseline) = set.get(baseline_lane, evidence_id) else {
            failures.push(format!(
                "missing evidence {evidence_id} for lane {baseline_lane}"
            ));
            continue;
        };
        for lane in &lanes[1..] {
            let Some(candidate) = set.get(lane, evidence_id) else {
                failures.push(format!("missing evidence {evidence_id} for lane {lane}"));
                continue;
            };
            for field in COMPARED_FIELDS {
                let left = baseline.provenance.get(field).unwrap_or_default();
                let right = candidate.provenance.get(field).unwrap_or_default();
                if left != right {
                    failures.push(format!(
                        "{evidence_id}: provenance.{field} differs ({baseline_lane}={left:?}, \
                         {lane}={right:?})"
                    ));
                }
            }
            let left = Json::Object(baseline.observed.clone().into_iter().collect());
            let right = Json::Object(candidate.observed.clone().into_iter().collect());
            for path in differing_paths(&left, &right, "observed") {
                failures.push(format!(
                    "{evidence_id}: {path} differs between {baseline_lane} and {lane}"
                ));
            }
        }
    }
    if failures.is_empty() {
        Ok(format!(
            "{} observation record(s) match across lanes {} (normalized provenance: {})",
            evidence_ids.len(),
            lanes.join(", "),
            NORMALIZED_FIELDS.join(", ")
        ))
    } else {
        failures.sort();
        failures.dedup();
        Err(failures)
    }
}

/// Returns the fully qualified paths at which two JSON values differ.
///
/// No key name is special here. A subtree keyed `runner` is compared exactly
/// like any other.
pub fn differing_paths(left: &Json, right: &Json, path: &str) -> Vec<String> {
    match (left, right) {
        (Json::Object(left_entries), Json::Object(right_entries)) => {
            let mut differences = Vec::new();
            let mut keys: Vec<&String> = left_entries.keys().chain(right_entries.keys()).collect();
            keys.sort();
            keys.dedup();
            for key in keys {
                match (left_entries.get(key), right_entries.get(key)) {
                    (Some(left_item), Some(right_item)) => differences.extend(differing_paths(
                        left_item,
                        right_item,
                        &format!("{path}.{key}"),
                    )),
                    _ => differences.push(format!("{path}.{key}")),
                }
            }
            differences
        }
        (Json::Array(left_items), Json::Array(right_items)) => {
            if left_items.len() != right_items.len() {
                return vec![path.to_owned()];
            }
            let mut differences = Vec::new();
            for (index, (left_item, right_item)) in
                left_items.iter().zip(right_items.iter()).enumerate()
            {
                differences.extend(differing_paths(
                    left_item,
                    right_item,
                    &format!("{path}[{index}]"),
                ));
            }
            differences
        }
        (left, right) if left == right => Vec::new(),
        _ => vec![path.to_owned()],
    }
}

#[cfg(test)]
mod tests {
    use super::differing_paths;
    use crate::json::parse;

    #[test]
    fn a_subtree_named_runner_is_still_compared() {
        let left = parse(r#"{"runner":{"outcome":"success"}}"#).expect("valid");
        let right = parse(r#"{"runner":{"outcome":"failure"}}"#).expect("valid");
        assert_eq!(
            differing_paths(&left, &right, "observed"),
            vec!["observed.runner.outcome".to_owned()]
        );
    }

    #[test]
    fn identical_documents_have_no_differences() {
        let left = parse(r#"{"a":[1,{"b":null}]}"#).expect("valid");
        let right = parse(r#"{"a":[1,{"b":null}]}"#).expect("valid");
        assert!(differing_paths(&left, &right, "observed").is_empty());
    }
}
