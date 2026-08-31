use std::env;
use std::process::ExitCode;

use fixture_harness::cache_payload;

fn main() -> ExitCode {
    let mut arguments = env::args().skip(1);
    let (Some(namespace), Some(key), None) = (arguments.next(), arguments.next(), arguments.next())
    else {
        eprintln!("usage: cache_payload NAMESPACE KEY");
        return ExitCode::from(2);
    };
    match cache_payload(&namespace, &key) {
        Ok(payload) => {
            print!("{}", String::from_utf8_lossy(&payload));
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("{error}");
            ExitCode::from(2)
        }
    }
}
