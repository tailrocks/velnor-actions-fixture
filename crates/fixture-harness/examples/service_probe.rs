use std::env;
use std::process::ExitCode;

use fixture_harness::probe_service;

fn main() -> ExitCode {
    let Some(address) = env::args().nth(1) else {
        eprintln!("usage: service_probe HOST:PORT");
        return ExitCode::from(2);
    };
    match probe_service(&address, b"fixture-ping\n") {
        Ok(reply) => {
            println!("digest={}", reply.digest);
            println!("response={:?}", String::from_utf8_lossy(&reply.response));
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("{error}");
            ExitCode::from(2)
        }
    }
}
