import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import core
from execution import History, outcome, process_alive
import rollback


def cli_log(*extra):
    lines = ['Verified 1/1 YAML files.', 'Executing step: Test', *extra,
             'Finished executing YAML stage: Test', 'Exiting.']
    return '\n'.join('[2026-11-01 12:00:00] [INFO]: '+line for line in lines)


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package = {'name': 'test.yaml', 'sha': 'a'*40, 'sig_sha': 'b'*40, 'revision': 'c'*40}
        self.history = History(self.root)
        self.folder = self.root / 'runs' / 'one'
        self.folder.mkdir(parents=True)

    def report(self, status, **extra):
        result = {**self.package, 'status': status, 'folder': str(self.folder), 'time': '2026-11-01', **extra}
        core.atomic_write(self.folder / 'run-result.json', json.dumps({'results': {'test.yaml': result}, 'complete': True}).encode())
        return result

    def test_zero_exit_does_not_hide_errors_skips_or_missing_logs(self):
        self.assertEqual(outcome(0, cli_log()), 'applied')
        self.assertEqual(outcome(1, cli_log()), 'failed')
        self.assertEqual(outcome(0, cli_log()+'\n[2026-11-01 12:00:00] [ERROR]: Access denied'), 'failed')
        self.assertEqual(outcome(0, cli_log('Skipping step due to conditions not met.')), 'skipped')
        self.assertEqual(outcome(0, ''), 'uncertain')
        self.assertEqual(outcome(0, cli_log()+'\n[2026-11-01 12:00:00] [WARN]: Warning'), 'uncertain')

    def test_success_survives_restart_and_tracks_exact_revision(self):
        self.history.begin(self.folder, [self.package])
        self.report('applied')
        self.history.finish(self.folder)
        reopened = History(self.root)
        self.assertEqual(reopened.status(self.package), 'applied')
        self.assertEqual(reopened.status({**self.package, 'sha': 'd'*40}), 'older')
        self.assertFalse(reopened.value['pending'])

    def test_failed_rerun_preserves_previous_success(self):
        self.history.begin(self.folder, [self.package])
        first = self.report('applied')
        self.history.finish(self.folder)
        self.history.begin(self.folder, [self.package])
        self.report('failed')
        self.history.finish(self.folder)
        self.assertEqual(self.history.status(self.package), 'failed')
        self.assertEqual(self.history.item('test.yaml')['applied'], first)

    def test_restore_status_clears_applied_but_does_not_erase_history(self):
        self.history.begin(self.folder, [self.package])
        self.report('applied')
        self.history.finish(self.folder)
        self.history.begin(self.folder, [self.package])
        self.report('restored')
        self.history.finish(self.folder)
        self.assertEqual(self.history.status(self.package), 'restored')
        self.assertIsNone(self.history.item('test.yaml')['applied'])

    def test_wrong_hash_and_abandoned_runs_are_not_marked_applied(self):
        self.history.begin(self.folder, [self.package])
        self.report('applied', sha='d'*40)
        self.history.finish(self.folder)
        self.assertEqual(self.history.status(self.package), 'uncertain')
        self.assertNotIn('applied', self.history.item('test.yaml'))
        self.history.begin(self.folder / 'missing', [self.package])
        self.history.finish(self.folder / 'missing', 'UAC cancelled')
        self.assertEqual(self.history.status(self.package), 'uncertain')

    def test_native_process_liveness_read(self):
        self.assertTrue(process_alive(os.getpid()))
        self.assertFalse(process_alive(0x7fffffff))

    def test_restart_after_host_never_started_is_unconfirmed(self):
        self.history.begin(self.folder, [self.package])
        self.history.value['pending'][str(self.folder)]['owner_pid'] = 0x7fffffff
        self.history.save()
        reopened = History(self.root)
        self.assertEqual(reopened.status(self.package), 'uncertain')
        self.assertFalse(reopened.value['pending'])

    def test_multiple_applies_can_restore_back_through_previous_records(self):
        for name in ('one', 'two', 'three'):
            self.folder = self.root / name
            self.folder.mkdir(exist_ok=True)
            self.history.begin(self.folder, [self.package])
            self.report('applied')
            self.history.finish(self.folder)
        for name, expected in (('three', 'two'), ('two', 'one'), ('one', None)):
            self.folder = self.root / name
            self.history.begin(self.folder, [self.package])
            self.report('restored')
            self.history.finish(self.folder)
            applied = self.history.item('test.yaml')['applied']
            self.assertEqual(Path(applied['folder']).name if applied else None, expected)
        self.folder = self.root / 'after-restore'
        self.folder.mkdir()
        self.history.begin(self.folder, [self.package])
        self.report('applied')
        self.history.finish(self.folder)
        self.assertEqual(self.history.status(self.package), 'applied')

    def test_host_forwards_console_preference_without_running_optimizer(self):
        with patch('rollback.user_sid', return_value='test-sid'), patch('core.run_program', return_value=0) as run:
            core.run_cli(Path(__file__), self.folder, auto_close=True)
            self.assertIn('--auto-close', run.call_args.args[1])
            self.assertIn('--sid', run.call_args.args[1])
            core.run_cli(Path(__file__), self.folder, auto_close=False)
            self.assertNotIn('--auto-close', run.call_args.args[1])


class RollbackTests(unittest.TestCase):
    def test_matching_snapshot_restores_and_verifies_original_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            backup = root / '0.hiv'
            backup.write_bytes(b'test fixture')
            item = {'hive': 'HKCU', 'path': 'Software\\Test', 'backup': '0.hiv',
                    'sha256': hashlib.sha256(backup.read_bytes()).hexdigest(), 'after': 'after', 'before': 'before', 'restored': False}
            manifest = root / 'undo.json'
            rollback.save_manifest(manifest, {'sid': 'test', 'roots': [item], 'ready': True})
            opened = MagicMock()
            opened.__enter__.return_value = 123
            with patch('rollback.user_sid', return_value='test'), patch('rollback.privileges'), \
                 patch('rollback.fingerprint', side_effect=['after', 'after', 'before']), \
                 patch('rollback.winreg.OpenKey', return_value=opened), patch('rollback.win32api.RegRestoreKey') as write:
                rollback.restore(manifest)
                write.assert_called_once_with(123, str(backup), 0)
            self.assertTrue(json.loads(manifest.read_text())['roots'][0]['restored'])

    def test_plan_rejects_scripts_services_and_hive_roots(self):
        self.assertIsNone(rollback.registry_plan('jobs: [{steps: [{name: x, exec: {commands: [x]}}]}]'))
        self.assertIsNone(rollback.registry_plan('jobs: [{steps: [{name: x, service: {stop: [SysMain]}}]}]'))
        source = 'jobs: [{steps: [{name: x, registry: {entries: [{hive: HKLM, path: Software, add: {x: {type: DWord, value: 1}}}]}}]}]'
        self.assertIsNone(rollback.registry_plan(source))
        self.assertEqual(rollback.registry_plan(source.replace('path: Software,', 'path: Software\\Test,')), [('HKLM', 'Software\\Test')])

    def test_conflict_in_any_subtree_blocks_every_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            backup = root / '0.hiv'
            backup.write_bytes(b'test fixture')
            item = {'hive': 'HKCU', 'path': 'Software\\Test', 'backup': '0.hiv',
                    'sha256': hashlib.sha256(backup.read_bytes()).hexdigest(), 'after': 'expected', 'before': 'before', 'restored': False}
            manifest = root / 'undo.json'
            rollback.save_manifest(manifest, {'sid': 'test', 'roots': [item], 'ready': True})
            with patch('rollback.user_sid', return_value='test'), patch('rollback.privileges'), \
                 patch('rollback.fingerprint', return_value='changed'), patch('rollback.win32api.RegRestoreKey') as write:
                with self.assertRaisesRegex(ValueError, 'Settings changed'):
                    rollback.restore(manifest)
                write.assert_not_called()
