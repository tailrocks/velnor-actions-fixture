use std::env;
use std::fs;
use std::path::PathBuf;
use std::process::ExitCode;

use fixture_harness::{Evidence, HarnessError};

fn main() -> ExitCode {
    match run(env::args().skip(1)) {
        Ok((json, output)) => {
            let result = match output {
                Some(path) => fs::write(&path, json).map_err(|error| {
                    HarnessError::from(format!(
                        "failed to write evidence {}: {error}",
                        path.display()
                    ))
                }),
                None => {
                    print!("{json}");
                    Ok(())
                }
            };
            match result {
                Ok(()) => ExitCode::SUCCESS,
                Err(error) => {
                    eprintln!("{error}");
                    ExitCode::from(2)
                }
            }
        }
        Err(error) => {
            eprintln!("{error}");
            ExitCode::from(2)
        }
    }
}

fn run(
    arguments: impl IntoIterator<Item = String>,
) -> Result<(String, Option<PathBuf>), HarnessError> {
    let mut arguments = arguments.into_iter();
    let mut scenario = None;
    let mut lane = None;
    let mut output = None;
    let mut fields = Vec::new();

    while let Some(argument) = arguments.next() {
        match argument.as_str() {
            "--scenario" => scenario = Some(next_value(&mut arguments, "--scenario")?),
            "--lane" => lane = Some(next_value(&mut arguments, "--lane")?),
            "--field" => fields.push(next_value(&mut arguments, "--field")?),
            "--output" => output = Some(PathBuf::from(next_value(&mut arguments, "--output")?)),
            _ => return Err(HarnessError::from(format!("unknown argument {argument:?}"))),
        }
    }

    let scenario = scenario.ok_or_else(|| HarnessError::from("missing --scenario"))?;
    let lane = lane.ok_or_else(|| HarnessError::from("missing --lane"))?;
    let mut evidence = Evidence::new(&scenario, &lane)?;
    for field in fields {
        let (key, value) = field
            .split_once('=')
            .ok_or_else(|| HarnessError::from(format!("field must be key=value: {field:?}")))?;
        evidence.insert(key, value)?;
    }
    Ok((evidence.to_json(), output))
}

fn next_value(
    arguments: &mut impl Iterator<Item = String>,
    option: &str,
) -> Result<String, HarnessError> {
    arguments
        .next()
        .ok_or_else(|| HarnessError::from(format!("missing value for {option}")))
}
