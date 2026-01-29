import os
import platform
from subprocess import call


def is_windows():
    return platform.system() == 'Windows'


current_dir = os.path.dirname(os.path.dirname(__file__))


proto_dir = os.path.join(current_dir, 'carball', 'generated')


def get_proto():
    # Check common environment variables
    for env_var in ['PROTOC_PATH', 'PROTOC']:
        val = os.getenv(env_var)
        if val:
            # Some actions set PROTOC to the actual binary path
            if os.path.exists(val):
                return val
            # Others might set it to the command name
            import shutil
            result = shutil.which(val)
            if result:
                return result

    import shutil
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


def split_to_list(drive_and_path):
    path = os.path.splitdrive(drive_and_path)[1]
    folders = []
    while 1:
        path, folder = os.path.split(path)

        if folder != "":
            folders.append(folder)
        else:
            if path != "":
                folders.append(path)

            break

    folders.reverse()
    return folders


def get_dir():
    return current_dir


def get_deepness(top_level_dir, path_list):
    return len(path_list) - path_list.index(top_level_dir)


def get_file_list(top_level_dir, exclude_dir=None, file_extension='.py'):
    proto_directories = [x[0] for x in os.walk(get_dir()) if top_level_dir in x[0] and '__pycache__' not in x[0]]

    file_result = []

    path_lists = []
    for path in proto_directories:
        if exclude_dir is not None and exclude_dir in path:
            continue
        path_list = split_to_list(path)
        try:
            deepness = get_deepness(top_level_dir, path_list)
        except ValueError:
            print(f"Skipping {path} because {top_level_dir} is not in {path_list}")
            continue
        left_over_paths = path_list[-deepness:]
        path_lists.append((path, deepness, left_over_paths))
    for path_item in path_lists:
        path = path_item[0]
        only_files = [(os.path.join(path, f), f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))
                      and file_extension in f and '__init__' not in f]
        for file in only_files:
            file_result.append((path_item[1], file[0]))
    return file_result


def create_proto_files():
    print('###CREATING PROTO FILES###')

    # Ensure the output directory exists
    os.makedirs(proto_dir, exist_ok=True)

    file_list = get_file_list(top_level_dir='api', file_extension='.proto')
    for file in file_list:
        path = file[0]
        file = file[1]
        print('creating proto file', file, end='\t')
        result = call([get_proto(), '--python_out=' + proto_dir, '--proto_path=' + current_dir, file])
        if result != 0:
            raise ValueError(result)
        print(result)


if __name__ == "__main__":
    create_proto_files()
