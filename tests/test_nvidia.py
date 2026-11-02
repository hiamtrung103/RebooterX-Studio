import copy
import ctypes
import json
import os
from pathlib import Path
import tempfile
import unittest

import nvidia as nv


class FakeDriver:
    def __init__(self, db):
        self.db = db
        self.profiles = copy.deepcopy(db['profiles'])
        self.applications = copy.deepcopy(db['applications'])

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass

    def profile(self, executable=None, create=False):
        key = self.applications.get(executable) if executable else 'Global'
        if key is None:
            if not create:
                return None, {'name': 'RebooterX · ' + executable, 'apps': 1, 'new': True}
            key = 'Created · ' + executable
            self.applications[executable] = key
            self.profiles[key] = {}
        return key, {'name': key, 'apps': sum(v == key for v in self.applications.values()), 'new': False}

    def named_profile(self, name):
        if name not in self.profiles:
            raise nv.NvError('Missing profile')
        return name

    def get(self, profile, identifier):
        return copy.deepcopy(self.profiles.get(profile, {}).get(identifier, {'value': None, 'explicit': False}))

    def set(self, profile, identifier, state):
        if identifier == self.db.get('reject'):
            raise nv.NvError('Setting unsupported')
        if state['explicit']:
            self.profiles[profile][identifier] = copy.deepcopy(state)
        else:
            self.profiles[profile].pop(identifier, None)

    def save(self):
        self.db['saves'] += 1
        self.db['profiles'], self.db['applications'] = self.profiles, self.applications


class NvidiaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.game = self.folder / 'game.exe'
        self.game.touch()
        self.db = {'profiles': {'Global': {}, 'Shared game profile': {}},
                   'applications': {'game.exe': 'Shared game profile', 'another.exe': 'Shared game profile'},
                   'saves': 0}
        self.service = nv.Profiles(self.folder / 'backups', lambda: FakeDriver(self.db))

    def test_game_profile_cache_scope_and_backup_restore_across_restart(self):
        self.db['profiles']['Shared game profile'][nv.POWER] = {'value': 0, 'explicit': True}
        plan = self.service.plan(str(self.game), {nv.POWER: 1, nv.CACHE: 0xFFFFFFFF, nv.QUALITY: 20})
        self.assertEqual(self.db['saves'], 0)
        self.assertEqual(plan['profile']['apps'], 2)
        self.assertTrue(next(c for c in plan['changes'] if c['id'] == nv.CACHE)['global'])
        path = self.service.apply(plan)
        self.assertEqual(self.db['saves'], 1)
        self.assertEqual(self.db['profiles']['Global'][nv.CACHE]['value'], 0xFFFFFFFF)
        self.assertNotIn(nv.CACHE, self.db['profiles']['Shared game profile'])
        receipt = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(receipt['status'], 'applied')
        restarted = nv.Profiles(self.service.folder, lambda: FakeDriver(self.db))
        restarted.restore()
        self.assertEqual(self.db['profiles']['Shared game profile'][nv.POWER]['value'], 0)
        self.assertNotIn(nv.QUALITY, self.db['profiles']['Shared game profile'])
        self.assertNotIn(nv.CACHE, self.db['profiles']['Global'])
        self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['status'], 'restored')

    def test_global_scope_and_new_game(self):
        self.service.apply(self.service.plan('', {nv.POWER: 1}))
        self.assertIn(nv.POWER, self.db['profiles']['Global'])
        self.db['applications'].clear()
        self.service.apply(self.service.plan(str(self.game), {nv.QUALITY: 20}))
        self.assertEqual(self.db['applications']['game.exe'], 'Created · game.exe')
        self.service.restore()
        self.assertNotIn(nv.QUALITY, self.db['profiles']['Created · game.exe'])

    def test_stale_preview_blocks_all_writes(self):
        plan = self.service.plan(str(self.game), {nv.POWER: 1, nv.CACHE: 0xFFFFFFFF})
        self.db['profiles']['Global'][nv.CACHE] = {'value': 1024, 'explicit': True}
        with self.assertRaises(nv.NvError):
            self.service.apply(plan)
        self.assertEqual(self.db['saves'], 0)
        self.assertNotIn(nv.POWER, self.db['profiles']['Shared game profile'])

    def test_restore_conflict_blocks_all_changes(self):
        self.service.apply(self.service.plan(str(self.game), {nv.POWER: 1, nv.CACHE: 0xFFFFFFFF}))
        self.db['profiles']['Global'][nv.CACHE]['value'] = 1024
        with self.assertRaises(nv.NvError):
            self.service.restore()
        self.assertEqual(self.db['saves'], 1)
        self.assertEqual(self.db['profiles']['Shared game profile'][nv.POWER]['value'], 1)

    def test_rejected_setting_discards_whole_session(self):
        self.db['reject'] = nv.QUALITY
        plan = self.service.plan(str(self.game), {nv.POWER: 1, nv.QUALITY: 20})
        with self.assertRaises(nv.NvError):
            self.service.apply(plan)
        self.assertEqual(self.db['saves'], 0)
        self.assertEqual(self.db['profiles']['Shared game profile'], {})
        self.assertEqual(json.loads(next(self.service.folder.glob('*.json')).read_text(encoding='utf-8'))['status'], 'aborted')

    def test_failed_backup_prevents_save(self):
        plan = self.service.plan(str(self.game), {nv.POWER: 1})
        self.service.write = lambda *_: (_ for _ in ()).throw(OSError('disk full'))
        with self.assertRaises(OSError):
            self.service.apply(plan)
        self.assertEqual(self.db['saves'], 0)

    def test_invalid_path_value_and_empty_selection(self):
        for path, choices in [('missing.exe', {nv.POWER: 1}), ('', {}), ('', {nv.POWER: 999})]:
            with self.assertRaises(nv.NvError):
                self.service.plan(path, choices)
        self.assertEqual(self.db['saves'], 0)

    def test_full_performance_preset_round_trip(self):
        before = copy.deepcopy(self.db['profiles'])
        self.assertEqual(nv.OPTIONS[nv.TRILINEAR]['On'], 0)
        self.assertEqual(nv.OPTIONS[nv.THREADED]['Auto'], 0)
        self.service.apply(self.service.plan(str(self.game), nv.PERFORMANCE_PRESET))
        self.assertEqual(len(self.db['profiles']['Shared game profile']), 9)
        self.service.restore()
        self.assertEqual(self.db['profiles'], before)

    @unittest.skipUnless(os.name == 'nt', 'Windows UTF-16 ABI')
    def test_public_nvapi_structure_layout(self):
        self.assertEqual(ctypes.sizeof(nv.Setting), 12320)
        self.assertEqual(ctypes.sizeof(nv.Application), 12296)
        self.assertEqual(ctypes.sizeof(nv.Profile), 4116)
        self.assertEqual(nv.structure(nv.Setting).version, 0x13020)


if __name__ == '__main__':
    unittest.main()
