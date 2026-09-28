import os
import platform
import shutil
from subprocess import call, check_output


def is_windows():
    return platform.system() == 'Windows'


current_dir = os.path.dirname(os.path.dirname(__file__))


proto_dir = os.path.join(current_dir, 'carball', 'generated')

# protoc 29.5 generates code requiring Python protobuf >=5.29.5.
# Keep this aligned with the runtime constraints and CI compiler versions.
PROTOC_VERSION = '29.5'


def get_proto():
    # Check common environment variables
    for env_var in ['PROTOC_PATH', 'PROTOC']:
        val = os.getenv(env_var)
        if val:
            # Some actions set PROTOC to the actual binary path
            if os.path.exists(val):
                return val
            # Others might set it to the command name
            result = shutil.which(val)
            if result:
                return result
            raise FileNotFoundError(f"{env_var}={val!r} does not name an existing protoc executable.")

    result = shutil.which('protoc')
    if result is not None:
        return result

    if is_windows():
        legacy_path = os.path.join(proto_dir, 'protoc.exe')
        if os.path.exists(legacy_path):
            return legacy_path
    else:
        for path in ['/usr/local/bin/protoc', '/usr/bin/protoc', '/opt/homebrew/bin/protoc']:
            if os.path.exists(path):
                return path
        
        legacy_path = os.path.join(proto_dir, 'binaries', 'protoc')
        if os.path.exists(legacy_path):
            return legacy_path
    
    print(f"DEBUG: PATH is {os.getenv('PATH')}")
    print(f"DEBUG: PROTOC env is {os.getenv('PROTOC')}")
    raise FileNotFoundError("Could not find 'protoc'. Please install protobuf compiler and ensure it is in your PATH, or set PROTOC_PATH.")


def validate_proto_version(protoc):
    version = check_output([protoc, '--version'], text=True).strip()
    if version != f'libprotoc {PROTOC_VERSION}':
        raise RuntimeError(
            f"Expected protoc {PROTOC_VERSION}, but {protoc!r} reports {version!r}. "
            "Using a different compiler can generate code incompatible with the "
            "protobuf runtime declared by this project. Install protoc "
            f"{PROTOC_VERSION} and set PROTOC_PATH to its executable."
        )


def get_dir():
    return current_dir


def get_file_list(top_level_dir, exclude_dir=None, file_extension='.py'):
    # Walk only the requested project directory, never matching copies in
    # virtualenvs, build output, or installed wheels elsewhere in the checkout.
    root = os.path.join(get_dir(), top_level_dir)
    file_result = []
    for path, directories, files in os.walk(root):
        directories[:] = sorted(d for d in directories if d != '__pycache__')
        if exclude_dir is not None and exclude_dir in path:
            directories[:] = []
            continue
        relative = os.path.relpath(path, root)
        deepness = 1 if relative == '.' else len(relative.split(os.sep)) + 1
        for name in sorted(files):
            if name.endswith(file_extension) and '__init__' not in name:
                file_result.append((deepness, os.path.join(path, name)))
    return file_result


def create_proto_files():
    print('###CREATING PROTO FILES###')

    # Reject incompatible compilers before rewriting any generated files.
    protoc = get_proto()
    validate_proto_version(protoc)

    # Ensure the output directory exists
    os.makedirs(proto_dir, exist_ok=True)

    file_list = get_file_list(top_level_dir='api', file_extension='.proto')
    for _, file in file_list:
        print('creating proto file', file, end='\t')
        result = call([protoc, '--python_out=' + proto_dir, '--proto_path=' + current_dir, file])
        if result != 0:
            raise ValueError(result)
        print(result)


if __name__ == "__main__":
    create_proto_files()
