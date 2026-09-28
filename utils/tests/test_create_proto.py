import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from utils.create_proto import create_proto_files, get_file_list, get_proto, validate_proto_version
from utils.import_fixer import convert_to_relative_imports


@patch.dict(os.environ, {}, clear=True)
class GetProtoTests(unittest.TestCase):
    @patch('utils.create_proto.os.path.exists', return_value=True)
    def test_with_env_var(self, exists):
        with patch.dict(os.environ, {'PROTOC_PATH': '/foo/bar/protoc'}):
            self.assertEqual(get_proto(), '/foo/bar/protoc')

    @patch('utils.create_proto.shutil.which', return_value='/tools/protoc')
    @patch('utils.create_proto.os.path.exists', return_value=False)
    def test_env_command_name(self, exists, which):
        with patch.dict(os.environ, {'PROTOC': 'protoc'}):
            self.assertEqual(get_proto(), '/tools/protoc')
        which.assert_called_once_with('protoc')

    @patch('utils.create_proto.shutil.which', return_value=None)
    @patch('utils.create_proto.os.path.exists', return_value=False)
    def test_invalid_override_does_not_fall_back(self, exists, which):
        with patch.dict(os.environ, {'PROTOC_PATH': '/missing/protoc'}):
            with self.assertRaisesRegex(FileNotFoundError, 'PROTOC_PATH'):
                get_proto()

    @patch('utils.create_proto.shutil.which', return_value='/tools/protoc')
    def test_path_lookup(self, which):
        self.assertEqual(get_proto(), '/tools/protoc')

    @patch('utils.create_proto.shutil.which', return_value=None)
    @patch('utils.create_proto.os.path.exists', side_effect=lambda p: p.endswith('protoc.exe'))
    @patch('utils.create_proto.is_windows', return_value=True)
    def test_windows_legacy_lookup(self, is_windows, exists, which):
        self.assertTrue(get_proto().endswith('protoc.exe'))


class ProtocVersionTests(unittest.TestCase):
    @patch('utils.create_proto.check_output', return_value='libprotoc 29.5\n')
    def test_supported_version(self, output):
        validate_proto_version('/tools/protoc')
        output.assert_called_once_with(['/tools/protoc', '--version'], text=True)

    @patch('utils.create_proto.check_output')
    def test_incompatible_versions(self, output):
        for version in ['libprotoc 36.0', 'libprotoc 29.3', 'unexpected output']:
            with self.subTest(version=version):
                output.return_value = version
                with self.assertRaisesRegex(RuntimeError, 'Install protoc 29.5'):
                    validate_proto_version('/tools/protoc')

    @patch('utils.create_proto.call')
    @patch('utils.create_proto.os.makedirs')
    @patch('utils.create_proto.check_output', return_value='libprotoc 36.0')
    @patch('utils.create_proto.get_proto', return_value='/tools/protoc')
    def test_incompatible_compiler_does_not_write_files(self, get_proto, output, mkdir, call):
        with self.assertRaises(RuntimeError):
            create_proto_files()
        mkdir.assert_not_called()
        call.assert_not_called()

    @patch('utils.create_proto.call', return_value=0)
    @patch('utils.create_proto.get_file_list', return_value=[(1, '/project/api/game.proto')])
    @patch('utils.create_proto.os.makedirs')
    @patch('utils.create_proto.check_output', return_value='libprotoc 29.5')
    @patch('utils.create_proto.get_proto', return_value='/tools/protoc')
    def test_generation_uses_validated_compiler(self, get_proto, output, mkdir, files, call):
        create_proto_files()
        get_proto.assert_called_once_with()
        self.assertEqual(call.call_args[0][0][0], '/tools/protoc')
        self.assertEqual(call.call_args[0][0][-1], '/project/api/game.proto')


class ProtoDirectoryTests(unittest.TestCase):
    def test_only_project_schemas_are_discovered(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ['api/game.proto', 'api/stats/goal.proto',
                         'api/game.proto.bak', 'target/venv/api/game.proto']:
                file = root / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.touch()
            with patch('utils.create_proto.get_dir', return_value=directory):
                self.assertEqual(
                    get_file_list('api', file_extension='.proto'),
                    [(1, str(root / 'api/game.proto')),
                     (2, str(root / 'api/stats/goal.proto'))],
                )

    def test_import_fixer_only_changes_project_generated_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / 'carball/generated/api/stats/test_pb2.py'
            installed = root / 'target/venv/carball/generated/api/stats/test_pb2.py'
            original = 'from api import player_pb2\n'
            for file in [project, installed]:
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(original)
            with patch('utils.create_proto.get_dir', return_value=directory), \
                    patch('utils.import_fixer.get_dir', return_value=directory):
                convert_to_relative_imports()
            self.assertEqual(project.read_text(), 'from ...api import player_pb2\n')
            self.assertEqual(installed.read_text(), original)
            self.assertTrue((project.parent / '__init__.py').exists())
            self.assertFalse((installed.parent / '__init__.py').exists())


if __name__ == '__main__':
    unittest.main()
