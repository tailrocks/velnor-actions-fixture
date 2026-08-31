use std::fs;
use std::io::{Read, Write};
use std::net::TcpListener;
use std::thread;

use fixture_harness::{
    artifact_tree, cache_payload, parse_command_file, probe_service, release_subject,
    render_artifact_tree, ReleaseArtifact,
};

#[test]
fn command_file_example_has_canonical_values() {
    let values = parse_command_file("scalar=ready\nmultiline<<END\nfirst\nsecond\nEND\n")
        .expect("example command file should parse");
    assert_eq!(
        values.into_iter().collect::<Vec<_>>(),
        vec![
            ("multiline".to_owned(), "first\nsecond".to_owned()),
            ("scalar".to_owned(), "ready".to_owned()),
        ]
    );
}

#[test]
fn artifact_tree_example_is_sorted_and_content_bound() {
    let root = temporary_directory("artifact-tree");
    fs::create_dir_all(root.join("nested")).expect("create nested fixture directory");
    fs::write(root.join("z.txt"), b"zeta").expect("write fixture artifact");
    fs::write(root.join("nested/a.txt"), b"alpha").expect("write nested fixture artifact");

    let rendered = render_artifact_tree(&artifact_tree(&root).expect("walk fixture artifacts"));
    assert_eq!(
        rendered,
        concat!(
            "directory\t0\tfnv1a64:cbf29ce484222325\tnested\n",
            "file\t5\tfnv1a64:8ac625bb85ed202b\tnested/a.txt\n",
            "file\t4\tfnv1a64:2230c2613766819f\tz.txt\n",
        )
    );
    fs::remove_dir_all(root).expect("remove fixture directory");
}

#[test]
fn cache_payload_example_is_canonical() {
    let payload = cache_payload("cargo", "linux-x86_64").expect("valid cache identity");
    assert_eq!(
        String::from_utf8(payload).expect("cache payload is UTF-8"),
        "velnor.fixture.cache.v1\nnamespace=cargo\nkey=linux-x86_64\ndigest=fnv1a64:3e438ae0087e7655\n"
    );
}

#[test]
fn service_probe_example_captures_response() {
    let listener = TcpListener::bind("127.0.0.1:0").expect("bind local fixture service");
    let address = listener.local_addr().expect("read fixture service address");
    let server = thread::spawn(move || {
        let (mut stream, _) = listener.accept().expect("accept fixture probe");
        let mut request = Vec::new();
        stream
            .read_to_end(&mut request)
            .expect("read fixture request");
        assert_eq!(request, b"fixture-ping\n");
        stream
            .write_all(b"fixture-pong\n")
            .expect("write fixture reply");
    });

    let reply = probe_service(&address.to_string(), b"fixture-ping\n")
        .expect("probe local fixture service");
    server.join().expect("fixture service thread should pass");
    assert_eq!(reply.response, b"fixture-pong\n");
}

#[test]
fn release_subject_example_is_stable() {
    let artifact =
        ReleaseArtifact::from_bytes("fixture.tar.gz", b"release").expect("valid artifact");
    let subject = release_subject("ABCDEF0123456789ABCDEF0123456789ABCDEF01", &[artifact])
        .expect("valid release subject");
    assert_eq!(
        subject,
        "{\"schema\":\"velnor.fixture.release-subject.v1\",\"source_sha\":\"abcdef0123456789abcdef0123456789abcdef01\",\"artifacts\":[{\"name\":\"fixture.tar.gz\",\"bytes\":7,\"digest\":\"fnv1a64:a63d4c9b882b10fe\"}]}\n"
    );
}

fn temporary_directory(name: &str) -> std::path::PathBuf {
    std::env::temp_dir().join(format!("velnor-fixture-{name}-{}", std::process::id()))
}
