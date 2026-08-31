//! Deterministic payloads and probes used by the Velnor workflow fixture.

use std::collections::{btree_map::Entry, BTreeMap};
use std::fmt::{self, Write as FmtWrite};
use std::fs;
use std::io::{Read, Write as IoWrite};
use std::net::{Shutdown, TcpStream};
use std::path::{Path, PathBuf};
use std::time::Duration;

/// Marker emitted by this crate's build script.
pub const BUILD_MARKER: &str = env!("FIXTURE_BUILD_MARKER");

const SERVICE_TIMEOUT: Duration = Duration::from_secs(2);
const MAX_SERVICE_RESPONSE_BYTES: u64 = 64 * 1024;

/// A deterministic-harness failure with user-facing context.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HarnessError {
    message: String,
}

impl HarnessError {
    fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
        }
    }
}

impl fmt::Display for HarnessError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.message)
    }
}

impl std::error::Error for HarnessError {}

impl From<String> for HarnessError {
    fn from(message: String) -> Self {
        Self { message }
    }
}

impl From<&str> for HarnessError {
    fn from(message: &str) -> Self {
        Self::new(message)
    }
}

/// Parses GitHub command-file `name=value` and heredoc records.
///
/// Duplicate names are rejected so evidence cannot depend on overwrite order.
///
/// # Errors
///
/// Returns an error for malformed records, invalid names, missing heredoc
/// terminators, or duplicate names.
pub fn parse_command_file(input: &str) -> Result<BTreeMap<String, String>, HarnessError> {
    let lines: Vec<&str> = input.lines().collect();
    let mut values = BTreeMap::new();
    let mut line_index = 0;

    while line_index < lines.len() {
        let line = lines[line_index];
        line_index += 1;
        if line.is_empty() {
            continue;
        }

        if let Some((name, delimiter)) = line.split_once("<<") {
            validate_name(name, line_index)?;
            if delimiter.is_empty() || delimiter.chars().any(char::is_whitespace) {
                return Err(HarnessError::new(format!(
                    "line {line_index}: heredoc delimiter must be non-empty and contain no whitespace"
                )));
            }

            let value_start = line_index;
            while line_index < lines.len() && lines[line_index] != delimiter {
                line_index += 1;
            }
            if line_index == lines.len() {
                return Err(HarnessError::new(format!(
                    "line {value_start}: missing heredoc terminator {delimiter}"
                )));
            }
            let value = lines[value_start..line_index].join("\n");
            line_index += 1;
            insert_unique(&mut values, name, value, value_start)?;
            continue;
        }

        let Some((name, value)) = line.split_once('=') else {
            return Err(HarnessError::new(format!(
                "line {line_index}: expected name=value or name<<delimiter"
            )));
        };
        validate_name(name, line_index)?;
        insert_unique(&mut values, name, value.to_owned(), line_index)?;
    }

    Ok(values)
}

fn validate_name(name: &str, line_number: usize) -> Result<(), HarnessError> {
    if name.is_empty()
        || !name
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-'))
    {
        return Err(HarnessError::new(format!(
            "line {line_number}: invalid command-file name {name:?}"
        )));
    }
    Ok(())
}

fn insert_unique(
    values: &mut BTreeMap<String, String>,
    name: &str,
    value: String,
    line_number: usize,
) -> Result<(), HarnessError> {
    match values.entry(name.to_owned()) {
        Entry::Vacant(entry) => {
            entry.insert(value);
            Ok(())
        }
        Entry::Occupied(_) => Err(HarnessError::new(format!(
            "line {line_number}: duplicate command-file name {name:?}"
        ))),
    }
}

/// Kind of filesystem object represented by an [`ArtifactEntry`].
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ArtifactKind {
    /// Directory entry.
    Directory,
    /// Regular-file entry.
    File,
    /// Symbolic-link entry. The digest covers the link target text.
    Symlink,
}

impl ArtifactKind {
    /// Stable lowercase representation used in fixture evidence.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Directory => "directory",
            Self::File => "file",
            Self::Symlink => "symlink",
        }
    }
}

/// One sorted entry in an artifact tree.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ArtifactEntry {
    /// Slash-separated path relative to the inspected root.
    pub path: String,
    /// Filesystem object kind.
    pub kind: ArtifactKind,
    /// File length or symlink-target text length. Directories are zero.
    pub bytes: u64,
    /// Stable FNV-1a digest for file contents or symlink target text.
    pub digest: String,
}

/// Walks an artifact directory without following symbolic links.
///
/// Entries are returned in path order. Digests are deterministic fixture
/// fingerprints, not cryptographic integrity proofs.
///
/// # Errors
///
/// Returns an error when the root is not a directory, an entry cannot be read,
/// or a relative path is not valid UTF-8.
pub fn artifact_tree(root: &Path) -> Result<Vec<ArtifactEntry>, HarnessError> {
    if !root.is_dir() {
        return Err(HarnessError::new(format!(
            "artifact root is not a directory: {}",
            root.display()
        )));
    }

    let mut paths = Vec::new();
    collect_paths(root, &mut paths)?;
    paths.sort();
    paths
        .into_iter()
        .map(|path| artifact_entry(root, &path))
        .collect()
}

fn collect_paths(directory: &Path, paths: &mut Vec<PathBuf>) -> Result<(), HarnessError> {
    let entries = fs::read_dir(directory).map_err(|error| {
        HarnessError::new(format!(
            "failed to read artifact directory {}: {error}",
            directory.display()
        ))
    })?;
    for entry in entries {
        let entry = entry.map_err(|error| {
            HarnessError::new(format!(
                "failed to read entry under {}: {error}",
                directory.display()
            ))
        })?;
        let path = entry.path();
        let metadata = fs::symlink_metadata(&path).map_err(|error| {
            HarnessError::new(format!(
                "failed to inspect artifact entry {}: {error}",
                path.display()
            ))
        })?;
        paths.push(path.clone());
        if metadata.is_dir() {
            collect_paths(&path, paths)?;
        }
    }
    Ok(())
}

fn artifact_entry(root: &Path, path: &Path) -> Result<ArtifactEntry, HarnessError> {
    let relative = path.strip_prefix(root).map_err(|error| {
        HarnessError::new(format!(
            "artifact entry {} is outside root {}: {error}",
            path.display(),
            root.display()
        ))
    })?;
    let path_text = normalized_relative_path(relative)?;
    let metadata = fs::symlink_metadata(path).map_err(|error| {
        HarnessError::new(format!(
            "failed to inspect artifact entry {}: {error}",
            path.display()
        ))
    })?;

    let (kind, bytes, digest) = if metadata.file_type().is_symlink() {
        let target = fs::read_link(path).map_err(|error| {
            HarnessError::new(format!(
                "failed to read artifact symlink {}: {error}",
                path.display()
            ))
        })?;
        let target = target.to_str().ok_or_else(|| {
            HarnessError::new(format!(
                "artifact symlink target is not UTF-8: {}",
                path.display()
            ))
        })?;
        (
            ArtifactKind::Symlink,
            target.len() as u64,
            stable_digest(target.as_bytes()),
        )
    } else if metadata.is_dir() {
        (ArtifactKind::Directory, 0, stable_digest(&[]))
    } else if metadata.is_file() {
        let contents = fs::read(path).map_err(|error| {
            HarnessError::new(format!(
                "failed to read artifact file {}: {error}",
                path.display()
            ))
        })?;
        (
            ArtifactKind::File,
            contents.len() as u64,
            stable_digest(&contents),
        )
    } else {
        return Err(HarnessError::new(format!(
            "unsupported artifact entry type: {}",
            path.display()
        )));
    };

    Ok(ArtifactEntry {
        path: path_text,
        kind,
        bytes,
        digest,
    })
}

fn normalized_relative_path(path: &Path) -> Result<String, HarnessError> {
    let mut output = String::new();
    for component in path.components() {
        let component = component.as_os_str().to_str().ok_or_else(|| {
            HarnessError::new(format!(
                "artifact path is not valid UTF-8: {}",
                path.display()
            ))
        })?;
        if !output.is_empty() {
            output.push('/');
        }
        output.push_str(component);
    }
    Ok(output)
}

/// Renders artifact entries as stable tab-separated evidence.
pub fn render_artifact_tree(entries: &[ArtifactEntry]) -> String {
    let mut output = String::new();
    for entry in entries {
        let _ = writeln!(
            output,
            "{}\t{}\t{}\t{}",
            entry.kind.as_str(),
            entry.bytes,
            entry.digest,
            entry.path
        );
    }
    output
}

/// Produces deterministic bytes for cold/warm cache workflow checks.
///
/// # Errors
///
/// Returns an error when namespace or key is empty or contains a newline.
pub fn cache_payload(namespace: &str, key: &str) -> Result<Vec<u8>, HarnessError> {
    validate_single_line("cache namespace", namespace)?;
    validate_single_line("cache key", key)?;
    let digest = stable_digest(format!("{namespace}\0{key}").as_bytes());
    Ok(
        format!("velnor.fixture.cache.v1\nnamespace={namespace}\nkey={key}\ndigest={digest}\n")
            .into_bytes(),
    )
}

fn validate_single_line(label: &str, value: &str) -> Result<(), HarnessError> {
    if value.is_empty() || value.contains(['\n', '\r']) {
        return Err(HarnessError::new(format!(
            "{label} must be non-empty and single-line"
        )));
    }
    Ok(())
}

/// Response captured from a bounded TCP service probe.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ServiceReply {
    /// Raw bytes returned by the service.
    pub response: Vec<u8>,
    /// Stable digest of the response bytes.
    pub digest: String,
}

/// Connects to a TCP service, sends a request, and captures a bounded response.
///
/// The fixed timeout and response limit prevent fixture jobs from hanging or
/// producing unbounded evidence.
///
/// # Errors
///
/// Returns an error for connection, timeout, write, shutdown, read, or response
/// size failures.
pub fn probe_service(address: &str, request: &[u8]) -> Result<ServiceReply, HarnessError> {
    validate_single_line("service address", address)?;
    let mut stream = TcpStream::connect(address)
        .map_err(|error| HarnessError::new(format!("failed to connect to {address}: {error}")))?;
    stream
        .set_read_timeout(Some(SERVICE_TIMEOUT))
        .map_err(|error| {
            HarnessError::new(format!("failed to set read timeout for {address}: {error}"))
        })?;
    stream
        .set_write_timeout(Some(SERVICE_TIMEOUT))
        .map_err(|error| {
            HarnessError::new(format!(
                "failed to set write timeout for {address}: {error}"
            ))
        })?;
    stream.write_all(request).map_err(|error| {
        HarnessError::new(format!(
            "failed to write service request to {address}: {error}"
        ))
    })?;
    stream.shutdown(Shutdown::Write).map_err(|error| {
        HarnessError::new(format!(
            "failed to finish service request to {address}: {error}"
        ))
    })?;

    let mut response = Vec::new();
    stream
        .take(MAX_SERVICE_RESPONSE_BYTES + 1)
        .read_to_end(&mut response)
        .map_err(|error| {
            HarnessError::new(format!(
                "failed to read service response from {address}: {error}"
            ))
        })?;
    if response.len() as u64 > MAX_SERVICE_RESPONSE_BYTES {
        return Err(HarnessError::new(format!(
            "service response from {address} exceeded {MAX_SERVICE_RESPONSE_BYTES} bytes"
        )));
    }
    let digest = stable_digest(&response);
    Ok(ServiceReply { response, digest })
}

/// One immutable input to a release subject.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReleaseArtifact {
    /// Logical artifact name.
    pub name: String,
    /// Artifact byte length.
    pub bytes: u64,
    /// Stable fixture digest of artifact contents.
    pub digest: String,
}

impl ReleaseArtifact {
    /// Creates a release artifact from a logical name and contents.
    ///
    /// # Errors
    ///
    /// Returns an error when the name is empty, absolute, contains backslashes,
    /// or contains `.` or `..` path components.
    pub fn from_bytes(name: &str, contents: &[u8]) -> Result<Self, HarnessError> {
        validate_artifact_name(name)?;
        Ok(Self {
            name: name.to_owned(),
            bytes: contents.len() as u64,
            digest: stable_digest(contents),
        })
    }
}

fn validate_artifact_name(name: &str) -> Result<(), HarnessError> {
    if name.is_empty()
        || name.starts_with('/')
        || name.contains(['\\', '\n', '\r'])
        || name
            .split('/')
            .any(|component| component.is_empty() || matches!(component, "." | ".."))
    {
        return Err(HarnessError::new(format!(
            "invalid release artifact name {name:?}"
        )));
    }
    Ok(())
}

/// Creates a canonical release subject sorted by artifact name.
///
/// # Errors
///
/// Returns an error when the source SHA is not exactly 40 hexadecimal
/// characters or artifact names are duplicated.
pub fn release_subject(
    source_sha: &str,
    artifacts: &[ReleaseArtifact],
) -> Result<String, HarnessError> {
    if source_sha.len() != 40 || !source_sha.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(HarnessError::new(
            "source SHA must be exactly 40 hexadecimal characters",
        ));
    }

    let mut sorted = artifacts.to_vec();
    sorted.sort_by(|left, right| left.name.cmp(&right.name));
    if sorted
        .windows(2)
        .any(|window| window[0].name == window[1].name)
    {
        return Err(HarnessError::new(
            "release subject contains duplicate artifact names",
        ));
    }

    let mut output = format!(
        "{{\"schema\":\"velnor.fixture.release-subject.v1\",\"source_sha\":\"{}\",\"artifacts\":[",
        source_sha.to_ascii_lowercase()
    );
    for (index, artifact) in sorted.iter().enumerate() {
        if index != 0 {
            output.push(',');
        }
        let _ = write!(
            output,
            "{{\"name\":\"{}\",\"bytes\":{},\"digest\":\"{}\"}}",
            json_escape(&artifact.name),
            artifact.bytes,
            artifact.digest
        );
    }
    output.push_str("]}\n");
    Ok(output)
}

/// Canonical lane evidence emitted by workflow scenarios.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Evidence {
    scenario: String,
    lane: String,
    fields: BTreeMap<String, String>,
}

impl Evidence {
    /// Creates empty evidence for one scenario and runner lane.
    ///
    /// # Errors
    ///
    /// Returns an error when scenario or lane is empty or contains a newline.
    pub fn new(scenario: &str, lane: &str) -> Result<Self, HarnessError> {
        validate_single_line("evidence scenario", scenario)?;
        validate_single_line("evidence lane", lane)?;
        Ok(Self {
            scenario: scenario.to_owned(),
            lane: lane.to_owned(),
            fields: BTreeMap::new(),
        })
    }

    /// Adds one unique evidence field.
    ///
    /// # Errors
    ///
    /// Returns an error when the key is invalid or already exists.
    pub fn insert(&mut self, key: &str, value: &str) -> Result<(), HarnessError> {
        validate_name(key, 0)
            .map_err(|_| HarnessError::new(format!("invalid evidence field name {key:?}")))?;
        match self.fields.entry(key.to_owned()) {
            Entry::Vacant(entry) => {
                entry.insert(value.to_owned());
                Ok(())
            }
            Entry::Occupied(_) => Err(HarnessError::new(format!(
                "duplicate evidence field {key:?}"
            ))),
        }
    }

    /// Renders canonical JSON with sorted fields and a final newline.
    pub fn to_json(&self) -> String {
        let mut output = format!(
            "{{\"schema\":\"velnor.fixture.evidence.v1\",\"scenario\":\"{}\",\"lane\":\"{}\",\"build\":\"{}\",\"fields\":{{",
            json_escape(&self.scenario),
            json_escape(&self.lane),
            json_escape(BUILD_MARKER)
        );
        for (index, (key, value)) in self.fields.iter().enumerate() {
            if index != 0 {
                output.push(',');
            }
            let _ = write!(
                output,
                "\"{}\":\"{}\"",
                json_escape(key),
                json_escape(value)
            );
        }
        output.push_str("}}\n");
        output
    }
}

/// Returns a stable FNV-1a fixture fingerprint.
pub fn stable_digest(bytes: &[u8]) -> String {
    let mut hash = 0xcbf2_9ce4_8422_2325_u64;
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x0000_0100_0000_01b3);
    }
    format!("fnv1a64:{hash:016x}")
}

fn json_escape(value: &str) -> String {
    let mut escaped = String::new();
    for character in value.chars() {
        match character {
            '"' => escaped.push_str("\\\""),
            '\\' => escaped.push_str("\\\\"),
            '\n' => escaped.push_str("\\n"),
            '\r' => escaped.push_str("\\r"),
            '\t' => escaped.push_str("\\t"),
            character if character.is_control() => {
                let _ = write!(escaped, "\\u{:04x}", character as u32);
            }
            character => escaped.push(character),
        }
    }
    escaped
}

#[cfg(test)]
mod tests {
    use super::{cache_payload, parse_command_file, release_subject, Evidence, ReleaseArtifact};

    #[test]
    fn command_file_supports_scalar_and_heredoc_values() {
        let parsed = parse_command_file("alpha=one\nbody<<EOF\ntwo\nthree\nEOF\n")
            .expect("valid command file should parse");
        assert_eq!(parsed.get("alpha").map(String::as_str), Some("one"));
        assert_eq!(parsed.get("body").map(String::as_str), Some("two\nthree"));
    }

    #[test]
    fn command_file_rejects_duplicate_names() {
        let error = parse_command_file("alpha=one\nalpha=two\n")
            .expect_err("duplicate names must fail closed");
        assert!(error.to_string().contains("duplicate"));
    }

    #[test]
    fn cache_payload_is_repeatable_and_bound_to_key() {
        let first = cache_payload("cargo", "linux-x86_64").expect("valid cache payload");
        let second = cache_payload("cargo", "linux-x86_64").expect("valid cache payload");
        let different = cache_payload("cargo", "linux-aarch64").expect("valid cache payload");
        assert_eq!(first, second);
        assert_ne!(first, different);
    }

    #[test]
    fn release_subject_sorts_artifacts() {
        let beta = ReleaseArtifact::from_bytes("dist/beta", b"beta").expect("valid artifact");
        let alpha = ReleaseArtifact::from_bytes("dist/alpha", b"alpha").expect("valid artifact");
        let subject = release_subject("0123456789abcdef0123456789abcdef01234567", &[beta, alpha])
            .expect("valid subject");
        assert!(subject.find("dist/alpha") < subject.find("dist/beta"));
    }

    #[test]
    fn evidence_sorts_and_escapes_fields() {
        let mut evidence = Evidence::new("cache", "github").expect("valid evidence identity");
        evidence.insert("zeta", "line\n2").expect("unique field");
        evidence.insert("alpha", "quoted\"").expect("unique field");
        assert_eq!(
            evidence.to_json(),
            "{\"schema\":\"velnor.fixture.evidence.v1\",\"scenario\":\"cache\",\"lane\":\"github\",\"build\":\"fixture-harness-build-v1\",\"fields\":{\"alpha\":\"quoted\\\"\",\"zeta\":\"line\\n2\"}}\n"
        );
    }
}
