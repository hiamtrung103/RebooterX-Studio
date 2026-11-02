from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import app
import bootstrap
import core


class StartupTests(unittest.TestCase):
    def test_non_admin_never_opens_ui_or_runs_cli(self):
        with patch('bootstrap.ensure_admin', return_value=1), patch('ui.StudioApp') as ui:
            self.assertEqual(app.main(), 1)
            ui.assert_not_called()

    def test_frozen_non_admin_is_rejected_even_without_manifest(self):
        with patch('bootstrap.is_admin', return_value=False), patch.object(sys, 'frozen', True, create=True):
            self.assertEqual(bootstrap.ensure_admin(), 1)

    def test_admin_continues(self):
        with patch('bootstrap.is_admin', return_value=True):
            self.assertIsNone(bootstrap.ensure_admin())

    def test_packaged_runner_dispatch_and_console_preference(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(sys, 'frozen', True, create=True), \
             patch('rollback.user_sid', return_value='test-sid'), patch('core.run_program', return_value=0) as run:
            core.run_host(Path(directory), ['--package', 'test.yaml'], auto_close=True)
            executable, command, *_ = run.call_args.args
            self.assertEqual(executable, Path(sys.executable))
            self.assertEqual(command[0], '--runner')
            self.assertNotIn(str(core.BASE / 'runner.py'), command)
            self.assertIn('--auto-close', command)


if __name__ == '__main__':
    unittest.main()
