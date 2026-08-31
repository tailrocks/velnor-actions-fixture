use fixture_harness::BUILD_MARKER;

#[test]
fn build_script_exports_fixed_marker() {
    assert_eq!(BUILD_MARKER, "fixture-harness-build-v1");
}
