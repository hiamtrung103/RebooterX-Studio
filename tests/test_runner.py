"""Real console plumbing against a harmless compiled fixture, never Windows tweaks."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import core
from execution import History
import rollback


class ConsoleHostTests(unittest.TestCase):
    def test_final_readkey_auto_close_and_persistent_per_package_results(self):
        compiler = Path('C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe')
        if not compiler.is_file():
            self.skipTest('.NET Framework C# compiler is unavailable')
        with tempfile.TemporaryDirectory(prefix='rebooterx-console-test-') as temporary:
            folder = Path(temporary)
            fixture = folder / 'fixture.exe'
            subprocess.run([str(compiler), '/nologo', '/out:'+str(fixture),
                str(Path(__file__).parent / 'fixtures' / 'ConsoleFixture.cs')],
                check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            packages = []
            for index in range(2):
                content, signature = b'jobs: []', b'fixture signature'
                package = {'name': f'test{index}.yaml', 'sha': core.git_hash(content),
                           'sig_sha': core.git_hash(signature), 'revision': 'a'*40}
                (folder / package['name']).write_bytes(content)
                (folder / (package['name']+'.sig')).write_bytes(signature)
                packages.append(package)
            (folder / 'selection.json').write_text(json.dumps({'packages': packages}))
            history = History(folder / 'isolated-data')
            history.begin(folder, packages)
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 0
            process = subprocess.Popen([sys.executable, str(core.BASE / 'runner.py'), '--exe', str(fixture),
                '--folder', str(folder), '--sid', rollback.user_sid(), '--auto-close'],
                creationflags=subprocess.CREATE_NEW_CONSOLE, startupinfo=startup)
            try:
                code = process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                self.fail('Host did not release the fixture ReadKey and close')
            report = json.loads((folder / 'run-result.json').read_text(encoding='utf-8'))
            self.assertEqual(code, 0, report)
            self.assertTrue(report['complete'])
            self.assertTrue(all(result['status'] == 'applied' for result in report['results'].values()))
            history.finish(folder)
            reopened = History(folder / 'isolated-data')
            self.assertTrue(all(reopened.status(package) == 'applied' for package in packages))
