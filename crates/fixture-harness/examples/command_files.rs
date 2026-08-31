use std::process::ExitCode;

use fixture_harness::parse_command_file;

fn main() -> ExitCode {
    let source = "scalar=ready\nmultiline<<END\nfirst\nsecond\nEND\n";
    match parse_command_file(source) {
        Ok(values) => {
            for (name, value) in values {
                println!("{name}={value:?}");
            }
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("{error}");
            ExitCode::from(2)
        }
    }
}
