use std::process::Command;
use std::env;

fn main() {
    // Only run this if we are building for Python (maturin)
    // or if we want protos generated during development.
    println!("cargo:rerun-if-changed=api/");
    println!("cargo:rerun-if-changed=utils/");

    let python = env::var("PYTHON").unwrap_or_else(|_| "python3".to_string());

    println!("cargo:warning=Generating protobuf files...");
    let status = Command::new(&python)
        .arg("utils/create_proto.py")
        .status()
        .expect("failed to execute create_proto.py");

    if !status.success() {
        panic!("Protobuf generation failed");
    }

    println!("cargo:warning=Fixing protobuf imports...");
    let status = Command::new(&python)
        .arg("utils/import_fixer.py")
        .status()
        .expect("failed to execute import_fixer.py");

    if !status.success() {
        panic!("Import fixer failed");
    }
}
