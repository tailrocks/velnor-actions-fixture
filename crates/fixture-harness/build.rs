fn main() {
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rustc-env=FIXTURE_BUILD_MARKER=fixture-harness-build-v1");
}
