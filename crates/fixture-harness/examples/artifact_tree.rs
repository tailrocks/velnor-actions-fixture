use std::env;
use std::path::Path;
use std::process::ExitCode;

use fixture_harness::{artifact_tree, render_artifact_tree};

fn main() -> ExitCode {
    let Some(root) = env::args().nth(1) else {
        eprintln!("usage: artifact_tree ROOT");
        return ExitCode::from(2);
    };
    match artifact_tree(Path::new(&root)) {
        Ok(entries) => {
            print!("{}", render_artifact_tree(&entries));
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("{error}");
            ExitCode::from(2)
        }
    }
}
