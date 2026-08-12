use std::collections::BTreeSet;

pub const CLOSURE: &str = include_str!("../../../.github/fixtures/l2/closure.json");

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClosureEntry {
    pub identity: String,
    pub uses: String,
    pub input: Option<String>,
}

pub fn closure_entries(source: &str) -> Result<Vec<ClosureEntry>, String> {
    let mut entries = Vec::new();
    let mut identity = None;
    let mut input = None;
    for raw in source.lines() {
        let line = raw.trim().trim_end_matches(',');
        if let Some(value) = json_string(line, "identity")? {
            identity = Some(value);
        }
        if let Some(value) = json_string(line, "input")? {
            input = Some(value);
        }
        if let Some(uses) = json_string(line, "uses")? {
            let identity = identity
                .take()
                .ok_or_else(|| "closure entry uses appears before identity".to_owned())?;
            entries.push(ClosureEntry {
                identity,
                uses,
                input: input.take(),
            });
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
        if let Some(input) = &entry.input {
            if input.contains("${{") {
                return Err(format!("admission/unresolved-expression: {input}"));
            }
            if input != "persist-credentials=false" {
                return Err(format!("admission/unknown-input: {input}"));
            }
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

pub fn validate_disposable_lock(input: &str) -> Result<(), String> {
    if input.lines().any(|line| line.trim() == "invalid = true") {
        return Err("mise/invalid-disposable-lock".to_owned());
    }
    if !input
        .lines()
        .any(|line| line.trim_start().starts_with("version = "))
    {
        return Err("mise/disposable-lock-missing-version".to_owned());
    }
    Ok(())
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
    use super::{deterministic_subject, validate_closure, validate_disposable_lock, CLOSURE};

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

    #[test]
    fn every_negative_class_fails_closed() {
        for (fixture, class) in [
            (
                include_str!("../../../.github/fixtures/l2/mutable-ref.json"),
                "mutable-ref",
            ),
            (
                include_str!("../../../.github/fixtures/l2/unknown-repository.json"),
                "unknown repository",
            ),
            (
                include_str!("../../../.github/fixtures/l2/unknown-input.json"),
                "unknown-input",
            ),
            (
                include_str!("../../../.github/fixtures/l2/unknown-subpath.json"),
                "unknown local action",
            ),
            (
                include_str!("../../../.github/fixtures/l2/unresolved-expression.json"),
                "unresolved-expression",
            ),
        ] {
            assert!(validate_closure(fixture).unwrap_err().contains(class));
        }
        assert!(validate_disposable_lock(include_str!(
            "../../../.github/fixtures/l2/invalid-mise.lock"
        ))
        .unwrap_err()
        .contains("invalid-disposable-lock"));
    }
}
