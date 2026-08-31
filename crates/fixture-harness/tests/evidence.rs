use std::process::Command;

#[test]
fn evidence_binary_emits_sorted_canonical_json() {
    let output = Command::new(env!("CARGO_BIN_EXE_evidence"))
        .args([
            "--scenario",
            "rust",
            "--lane",
            "velnor",
            "--field",
            "toolchain=stable",
            "--field",
            "package=fixture-harness",
        ])
        .output()
        .expect("run evidence binary");
    assert!(
        output.status.success(),
        "evidence process failed: {output:?}"
    );
    assert_eq!(
        String::from_utf8(output.stdout).expect("evidence stdout is UTF-8"),
        "{\"schema\":\"velnor.fixture.evidence.v1\",\"scenario\":\"rust\",\"lane\":\"velnor\",\"build\":\"fixture-harness-build-v1\",\"fields\":{\"package\":\"fixture-harness\",\"toolchain\":\"stable\"}}\n"
    );
}

#[test]
fn evidence_binary_rejects_duplicate_fields() {
    let output = Command::new(env!("CARGO_BIN_EXE_evidence"))
        .args([
            "--scenario",
            "rust",
            "--lane",
            "github",
            "--field",
            "result=pass",
            "--field",
            "result=fail",
        ])
        .output()
        .expect("run evidence binary");
    assert_eq!(output.status.code(), Some(2));
    assert!(String::from_utf8(output.stderr)
        .expect("evidence stderr is UTF-8")
        .contains("duplicate evidence field"));
}
