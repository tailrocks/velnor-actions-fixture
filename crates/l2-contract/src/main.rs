use std::{env, fs, process::ExitCode};

use l2_contract::{deterministic_subject, validate_closure, CLOSURE};

fn main() -> ExitCode {
    match run() {
        Ok(output) => {
            print!("{output}");
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("{error}");
            ExitCode::from(2)
        }
    }
}

fn run() -> Result<String, String> {
    let mut args = env::args().skip(1);
    match (args.next().as_deref(), args.next(), args.next()) {
        (Some("validate"), None, None) => {
            let entries = validate_closure(CLOSURE)?;
            Ok(format!("closure-valid={}\n", entries.len()))
        }
        (Some("validate-file"), Some(path), None) => {
            let input = fs::read_to_string(&path).map_err(|error| format!("{path}: {error}"))?;
            validate_closure(&input)?;
            Ok("closure-valid=true\n".to_owned())
        }
        (Some("subject"), Some(source_sha), None) => deterministic_subject(&source_sha),
        _ => {
            Err("usage: l2-contract validate | validate-file PATH | subject SOURCE_SHA".to_owned())
        }
    }
}
