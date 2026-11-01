import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import core
from memory import MemReduct, architecture, check_hash, manifest_hash, PROJECT


class MemoryTests(unittest.TestCase):
    def test_manifest_distinguishes_architectures(self):
        manifest = '\n'.join((
            'a'*64 + ' *portable.7z', '#32-bit', 'b'*64 + ' *memreduct.exe',
            '#64-bit', 'c'*64 + ' *memreduct.exe', '#arm64', 'd'*64 + ' *memreduct.exe'))
        self.assertEqual(manifest_hash(manifest, 'portable.7z'), 'a'*64)
        for section, digest in (('32', 'b'), ('64', 'c'), ('arm64', 'd')):
            self.assertEqual(manifest_hash(manifest, 'memreduct.exe', section), digest*64)
        with self.assertRaises(ValueError):
            manifest_hash(manifest, 'unknown.exe')

    def test_checksum_rejects_corruption(self):
        with self.assertRaises(ValueError):
            check_hash(b'changed', hashlib.sha256(b'original').hexdigest())

    def test_native_architecture_overrides_32_bit_python(self):
        with patch.dict('os.environ', {'PROCESSOR_ARCHITEW6432': 'ARM64'}):
            self.assertEqual(architecture(), 'arm64')
        with patch.dict('os.environ', {'PROCESSOR_ARCHITEW6432': 'AMD64'}):
            self.assertEqual(architecture(), '64')

    def test_launch_verifies_installed_exe_and_exact_cleanup_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            tool = MemReduct(Path(temporary))
            tool.folder.mkdir(parents=True)
            content = b'MZ-test-file-never-executed'
            exe = tool.folder / 'memreduct.exe'
            exe.write_bytes(content)
            (tool.folder / 'verified.json').write_text(json.dumps({'sha256': hashlib.sha256(content).hexdigest()}))
            with patch.object(core, 'run_program', return_value=0) as run:
                for mode, args, wait in ((None, [], False), ('default', ['-clean'], True), ('full', ['-clean:full'], True)):
                    tool.launch(mode)
                    self.assertEqual(run.call_args.args[:2], (exe, args))
                    self.assertEqual(run.call_args.kwargs['wait'], wait)
                run.reset_mock()
                with self.assertRaises(ValueError):
                    tool.launch('arbitrary')
                run.assert_not_called()
                exe.write_bytes(b'corrupted')
                self.assertIsNone(tool.installed())
                with self.assertRaises(ValueError):
                    tool.launch('full')
                run.assert_not_called()

    def test_external_release_url_rejected_before_download(self):
        with tempfile.TemporaryDirectory() as temporary:
            tool = MemReduct(Path(temporary))
            release = {'assets': [
                {'name': 'test-bin.7z', 'browser_download_url': PROJECT+'/releases/download/x/a.7z'},
                {'name': 'test.sha256', 'browser_download_url': 'https://example.com/hash'}]}
            with patch('memory.seven_zip', return_value='7z.exe'), \
                 patch.object(tool.repo, 'request', return_value=json.dumps(release).encode()) as request:
                with self.assertRaises(ValueError):
                    tool.install()
                self.assertEqual(request.call_count, 1)

    def test_bad_archive_never_reaches_extractor(self):
        with tempfile.TemporaryDirectory() as temporary:
            tool = MemReduct(Path(temporary))
            release = {'assets': [
                {'name': 'test-bin.7z', 'browser_download_url': PROJECT+'/releases/download/x/a.7z'},
                {'name': 'test.sha256', 'browser_download_url': PROJECT+'/releases/download/x/h.sha256'}]}
            responses = [json.dumps(release).encode(), ('a'*64 + ' *test-bin.7z').encode(), b'wrong']
            with patch('memory.seven_zip', return_value='7z.exe'), \
                 patch.object(tool.repo, 'request', side_effect=responses), \
                 patch('memory.subprocess.run') as extract:
                with self.assertRaises(ValueError):
                    tool.install()
                extract.assert_not_called()
            self.assertFalse(tool.folder.exists())
