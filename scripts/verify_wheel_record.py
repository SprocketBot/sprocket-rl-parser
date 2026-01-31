import base64
import csv
import hashlib
import sys
import zipfile
from pathlib import Path


def iter_wheels(path: Path):
    if path.is_file() and path.suffix == ".whl":
        yield path
        return
    if path.is_dir():
        yield from path.glob("*.whl")
        return
    raise FileNotFoundError(f"Wheel not found: {path}")


def parse_record_row(row):
    if len(row) < 3:
        return None, None, None
    return row[0], row[1], row[2]


def decode_hash(value):
    if not value:
        return None, None
    algo, b64 = value.split("=", 1)
    return algo, base64.urlsafe_b64decode(b64 + "==")


def compute_hash(algo, data):
    h = hashlib.new(algo)
    h.update(data)
    return h.digest()


def verify_wheel(wheel_path: Path) -> bool:
    ok = True
    with zipfile.ZipFile(wheel_path) as zf:
        record_paths = [p for p in zf.namelist() if p.endswith(".dist-info/RECORD")]
        if not record_paths:
            print(f"[FAIL] {wheel_path.name}: RECORD not found")
            return False

        record_path = record_paths[0]
        with zf.open(record_path) as record_file:
            record_rows = list(csv.reader(record_file.read().decode("utf-8").splitlines()))

        for row in record_rows:
            file_path, hash_value, size_value = parse_record_row(row)
            if not file_path or file_path == record_path:
                continue
            normalized_path = file_path.replace("\\", "/")
            try:
                data = zf.read(normalized_path)
            except KeyError:
                print(f"[FAIL] {wheel_path.name}: missing file {file_path}")
                ok = False
                continue

            algo, expected = decode_hash(hash_value)
            if algo:
                actual = compute_hash(algo, data)
                if actual != expected:
                    print(f"[FAIL] {wheel_path.name}: hash mismatch for {file_path}")
                    ok = False
            if size_value:
                if int(size_value) != len(data):
                    print(f"[FAIL] {wheel_path.name}: size mismatch for {file_path}")
                    ok = False

    if ok:
        print(f"[OK] {wheel_path.name}")
    return ok


def main():
    if len(sys.argv) < 2:
        print("Usage: verify_wheel_record.py <wheel_or_dir> [...]")
        sys.exit(2)

    success = True
    for arg in sys.argv[1:]:
        for wheel in iter_wheels(Path(arg)):
            if not verify_wheel(wheel):
                success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
