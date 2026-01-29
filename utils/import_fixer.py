import os
import shutil
from tempfile import mkstemp

try:
    from .create_proto import get_file_list, get_dir
except ImportError:
    from create_proto import get_file_list, get_dir

import_statement = 'import '
from_import_statement = 'from '


def analyze_file(deepness, file_path, top_level_import):
    replace_map = dict()
    fh, abs_path = mkstemp()
    modified = False
    with os.fdopen(fh, 'w') as new_file:
        with open(file_path, 'r') as old_file:
            lines = old_file.readlines()
            for i in range(len(lines)):
                line = lines[i]
                extra_cases = '.' in line and top_level_import in line and not (import_statement + '.') in line

                # Handle "from api.X.Y import Z" or "from api import X" style imports
                if line.startswith(from_import_statement) and top_level_import in line and ' import ' in line:
                    # Extract the module path (e.g., "api.stats" from "from api.stats import stats_pb2 as ...")
                    parts = line.split(' import ')
                    if len(parts) == 2:
                        from_part = parts[0][len(from_import_statement):].strip()
                        import_part = parts[1].strip()

                        # Only process if it starts with our top_level_import
                        if from_part.startswith(top_level_import):
                            # The file is at depth 'deepness' from 'generated' directory
                            # e.g., for generated/api/stats/events_pb2.py, deepness=3 (generated, api, stats)
                            #
                            # For "from api import X":
                            #   - We need to go up (deepness-1) to get to 'generated'
                            #   - Then go into 'api' to find X
                            #   - Result: "from ..api import X" (for deepness=3)
                            #
                            # For "from api.stats import X":
                            #   - We need to go up (deepness-1) to get to 'generated'
                            #   - Then go into 'api/stats' to find X
                            #   - Result: "from ..api.stats import X" (for deepness=3)

                            if from_part == top_level_import:
                                # "from api import X" -> "from ..api import X"
                                # Go up (deepness-1) levels, then into top_level_import
                                dots = '.' * (deepness)
                                line = 'from ' + dots + top_level_import + ' import ' + import_part + '\n'
                                modified = True
                            elif from_part.startswith(top_level_import + '.'):
                                # "from api.stats import X" -> "from ..api.stats import X" or "from . import X"
                                # Check if the subpath matches our current directory
                                subpath = from_part[len(top_level_import) + 1:]  # Remove "api."

                                # For deepness=3, we're in api/stats/
                                # If importing from api.stats, that's our current dir, use "."
                                # If importing from api.metadata, use "../api/metadata"
                                dots = '.' * (deepness)
                                line = 'from ' + dots + from_part + ' import ' + import_part + '\n'
                                modified = True

                # Handle "import api.X" style imports
                elif line.startswith(import_statement) and extra_cases:
                    cut_line = line[len(import_statement):].rstrip()
                    ending_string = cut_line[cut_line.rfind('.') + 1:]
                    replace_map[cut_line] = ending_string
                    line = 'from ' + '.' * deepness + cut_line[:cut_line.rfind(ending_string) - 1] + ' import ' + ending_string + '\n'
                    modified = True
                else:
                    for key in replace_map:
                        if key in line:
                            modified = True
                            line = line.replace(key, replace_map[key])
                new_file.write(line)
    if modified:
        os.remove(file_path)
        shutil.move(abs_path, file_path)
        print(str(len(replace_map)), 'imports')
    else:
        print('not modified')


def add_inits(top_level_dir):
    proto_dir = [x[0] for x in os.walk(get_dir()) if top_level_dir in x[0] and '__pycache__' not in x[0]]
    for directory in proto_dir:
        with open(os.path.join(directory, '__init__.py'), 'w') as file:
            print('creating', file.name)


def convert_to_relative_imports(top_level_dir='generated', exclude_dir=None, top_level_import="api"):
    print('###FIXING IMPORTS###')
    file_list = get_file_list(top_level_dir, exclude_dir)
    for file in file_list:
        print('fixing file: ', file[1], end='\t')
        analyze_file(file[0], file[1], top_level_import)
    add_inits(top_level_dir)


# prevent_leaks("carball", "generated", "carball")
if __name__ == '__main__':
    convert_to_relative_imports()

"""
Hi All  This file converts protobuf imports to relative imports so instead of
import api.player_pb2
it does
import ...api.player_pb2

The reason for this is described here:
https://github.com/protocolbuffers/protobuf/issues/1491

Basically google does not allow relative imports from their generated protobuf code.
So we do it so that our genreated file can go in a folder we dont care about

"""
