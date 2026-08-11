use std::collections::BTreeSet;

pub const CLOSURE: &str = include_str!("../../../.github/fixtures/l2/closure.json");

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClosureEntry {
    pub identity: String,
    pub uses: String,
}

pub fn closure_entries(input: &str) -> Result<Vec<ClosureEntry>, String> {
    let mut entries = Vec::new();
    let mut identity = None;
    for raw in input.lines() {
        let line = raw.trim().trim_end_matches(',');
        if let Some(value) = json_string(line, "identity")? {
            identity = Some(value);
        }
        if let Some(uses) = json_string(line, "uses")? {
            let identity = identity
                .take()
                .ok_or_else(|| "closure entry uses appears before identity".to_owned())?;
            entries.push(ClosureEntry { identity, uses });
        }
    }
    if identity.is_some() || entries.is_empty() {
        return Err("closure contains an incomplete or empty entry".to_owned());
    }
    Ok(entries)
}

fn json_string(line: &str, key: &str) -> Result<Option<String>, String> {
    let prefix = format!("\"{key}\": \"");
    let Some(value) = line.strip_prefix(&prefix) else {
        return Ok(None);
    };
    let Some(value) = value.strip_suffix('"') else {
        return Err(format!("{key} is not a canonical JSON string"));
    };
    if value.is_empty() || value.contains(['"', '\\']) {
        return Err(format!("{key} is empty or escaped"));
    }
    Ok(Some(value.to_owned()))
}

pub fn validate_closure(input: &str) -> Result<Vec<ClosureEntry>, String> {
    let entries = closure_entries(input)?;
    let mut identities = BTreeSet::new();
    for entry in &entries {
        if !identities.insert(&entry.identity) {
            return Err(format!("duplicate identity: {}", entry.identity));
        }
        if entry.uses.starts_with("./") {
            if !matches!(
                entry.uses.as_str(),
                "./.github/actions/l2-root" | "./.github/actions/l2-nested"
            ) {
                return Err(format!("unknown local action: {}", entry.uses));
            }
            continue;
        }
        let Some((repository, reference)) = entry.uses.rsplit_once('@') else {
            return Err(format!("unresolved action: {}", entry.uses));
        };
        if repository != "actions/checkout" {
            return Err(format!("unknown repository: {repository}"));
        }
        if reference.len() != 40 || !reference.bytes().all(|byte| byte.is_ascii_hexdigit()) {
            return Err(format!("admission/mutable-ref: {}", entry.uses));
        }
    }
    Ok(entries)
}

pub fn deterministic_subject(source_sha: &str) -> Result<String, String> {
    if source_sha.len() != 40 || !source_sha.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err("source SHA must be exactly 40 hexadecimal characters".to_owned());
    }
    Ok(format!(
        "{{\"schema\":\"velnor.fixture.l2-subject.v1\",\"source_sha\":\"{}\",\"workload\":\"cargo-nextest-workspace-locked\"}}\n",
        source_sha.to_ascii_lowercase()
    ))
}

#[cfg(test)]
mod tests {
    use super::{deterministic_subject, validate_closure, CLOSURE};

    #[test]
    fn checked_in_closure_is_complete_and_immutable() {
        let entries = validate_closure(CLOSURE).expect("checked-in closure must validate");
        assert_eq!(entries.len(), 3);
        assert!(entries
            .iter()
            .any(|entry| entry.identity == "remote-checkout"));
    }

    #[test]
    fn mutable_remote_ref_fails_closed() {
        let invalid = CLOSURE.replace(
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            "actions/checkout@main",
        );
        assert!(validate_closure(&invalid)
            .unwrap_err()
            .contains("admission/mutable-ref"));
    }

    #[test]
    fn deterministic_subject_rejects_unbound_source() {
        assert!(deterministic_subject("main").is_err());
        let sha = "0123456789abcdef0123456789abcdef01234567";
        assert_eq!(
            deterministic_subject(sha).unwrap(),
            deterministic_subject(sha).unwrap()
        );
    }
}
