use std::env;
use std::fs;
use std::path::Path;
use std::process::ExitCode;

use fixture_harness::{release_subject, HarnessError, ReleaseArtifact};

fn main() -> ExitCode {
    match run() {
        Ok(subject) => {
            print!("{subject}");
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("{error}");
            ExitCode::from(2)
        }
    }
}

fn run() -> Result<String, HarnessError> {
    let mut arguments = env::args().skip(1);
    let source_sha = arguments
        .next()
        .ok_or_else(|| HarnessError::from("usage: release_subject SOURCE_SHA ARTIFACT..."))?;
    let paths: Vec<String> = arguments.collect();
    if paths.is_empty() {
        return Err(HarnessError::from(
            "usage: release_subject SOURCE_SHA ARTIFACT...",
        ));
    }

    let mut artifacts = Vec::new();
    for path in paths {
        let contents = fs::read(&path).map_err(|error| {
            HarnessError::from(format!("failed to read release artifact {path}: {error}"))
        })?;
        let name = Path::new(&path)
            .file_name()
            .and_then(|name| name.to_str())
            .ok_or_else(|| HarnessError::from(format!("invalid artifact path {path:?}")))?;
        artifacts.push(ReleaseArtifact::from_bytes(name, &contents)?);
    }
    release_subject(&source_sha, &artifacts)
}
