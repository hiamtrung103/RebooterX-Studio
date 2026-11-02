"""Small public NVAPI DRS adapter. No registry tweaks or bundled driver DLLs.

ABI/IDs: github.com/NVIDIA/nvapi (nvapi.h, nvapi_interface.h,
NvApiDriverSettings.h). Driver sessions are discarded unless SaveSettings succeeds.
"""
from __future__ import annotations

import ctypes as C
from pathlib import Path
import json
import os
import time
import uuid

from core import atomic_write

U32, HANDLE = C.c_uint32, C.c_void_p
WSTR = C.c_wchar * 2048


class Value(C.Union):
    _pack_ = 4
    _fields_ = [('dword', U32), ('raw', C.c_ubyte * 4100)]


class Setting(C.Structure):
    _pack_ = 4
    _fields_ = [('version', U32), ('name', WSTR), ('id', U32),
                ('type', U32), ('location', U32), ('predefined', U32),
                ('valid', U32), ('default', Value), ('current', Value)]


class Application(C.Structure):
    _fields_ = [('version', U32), ('predefined', U32), ('name', WSTR),
                ('friendly', WSTR), ('launcher', WSTR)]


class Profile(C.Structure):
    _fields_ = [('version', U32), ('name', WSTR), ('gpu', U32),
                ('predefined', U32), ('apps', U32), ('settings', U32)]


def structure(cls):
    value = cls()
    value.version = C.sizeof(cls) | (1 << 16)
    return value


POWER = 0x1057EB71
CACHE = 0x00AC8497
QUALITY = 0x00CE2691
VSYNC = 0x00A879CF
FPS_LIMIT = 0x10835002
ANISO_SAMPLE = 0x00E73211
TRILINEAR = 0x002ECAF2
THREADED = 0x20C1221E
FXAA = 0x1074C972
REFRESH = 0x0064B541
# Values from NVIDIA's public SDK. Cache size is in MiB, not VRAM allocation.
OPTIONS = {
    POWER: {'Prefer maximum performance': 1, 'Optimal power': 5, 'Adaptive': 0},
    CACHE: {'Unlimited': 0xFFFFFFFF, '100 GB': 102400, '10 GB': 10240,
            '5 GB': 5120, '1 GB': 1024},
    QUALITY: {'High performance': 20, 'Performance': 10, 'Quality': 0,
              'High quality': 0xFFFFFFF6},
    VSYNC: {'Off': 0x08416747, 'Use the 3D application setting': 0x60925292,
            'On': 0x47814940, 'Fast': 0x18888888},
    FPS_LIMIT: {'Off': 0, **{f'{fps} FPS': fps for fps in (30, 60, 90, 120, 141, 144, 162, 165, 237, 240, 360, 500)}},
    ANISO_SAMPLE: {'On': 1, 'Off': 0},
    # SDK calls this DISABLE_TRILIN_SLOPE: 0 enables the optimization.
    TRILINEAR: {'On': 0, 'Off': 1},
    THREADED: {'Auto': 0, 'On': 1, 'Off': 2},
    FXAA: {'Off': 0, 'On': 1},
    REFRESH: {'Highest available': 1, 'Application-controlled': 0},
}
NAMES = {POWER: 'Power management mode', CACHE: 'Shader Cache Size (global)',
         QUALITY: 'Texture filtering - Quality', VSYNC: 'Vertical sync',
         FPS_LIMIT: 'Max Frame Rate', ANISO_SAMPLE: 'Texture filtering - Anisotropic sample optimization',
         TRILINEAR: 'Texture filtering - Trilinear optimization', THREADED: 'Threaded optimization (OpenGL)',
         FXAA: 'Antialiasing - FXAA', REFRESH: 'Preferred refresh rate'}
PERFORMANCE_PRESET = {identifier: next(iter(values.values())) for identifier, values in OPTIONS.items()}


class NvError(RuntimeError):
    pass


class Driver:
    """A single, short-lived session. Call only on one worker thread."""
    def __init__(self):
        if os.name != 'nt':
            raise NvError('NVIDIA NVAPI requires Windows.')
        try:
            # Restrict DLL search to Windows System32, never the working directory.
            self.dll = C.CDLL('nvapi64.dll' if C.sizeof(HANDLE) == 8 else 'nvapi.dll',
                              winmode=0x00000800)
        except OSError as error:
            raise NvError('NVIDIA driver / NVAPI is unavailable. Install the NVIDIA driver first.') from error
        self.query = self.dll.nvapi_QueryInterface
        self.query.argtypes, self.query.restype = [U32], HANDLE
        self.functions = {}
        self.session = HANDLE()
        try:
            self.call(0x0150E828, [])
        except NvError as error:
            raise NvError('NVAPI initialization failed: no accessible NVIDIA GPU/driver was detected. '
                          + str(error)) from error
        try:
            self.call(0x0694D52E, [C.POINTER(HANDLE)], C.byref(self.session))
            self.call(0x375DBD6B, [HANDLE], self.session)
        except Exception:
            self.close()
            raise

    def call(self, identifier, signature, *args, allow=()):
        if identifier not in self.functions:
            pointer = self.query(identifier)
            if not pointer:
                raise NvError(f'NVAPI function unavailable: {identifier:#x}')
            self.functions[identifier] = C.CFUNCTYPE(C.c_int, *signature)(pointer)
        code = self.functions[identifier](*args)
        if code and code not in allow:
            hint = ' Run Studio as administrator and retry.' if code == -137 else ''
            raise NvError(f'NVAPI {identifier:#x} returned {code}.{hint}')
        return code

    def close(self):
        try:
            if self.session:
                self.call(0xDAD9CFF8, [HANDLE], self.session)
                self.session = HANDLE()
        finally:
            self.call(0xD22BDD7E, [])

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def profile(self, executable=None, create=False):
        handle = HANDLE()
        if not executable:
            self.call(0xDA8466A0, [HANDLE, C.POINTER(HANDLE)], self.session, C.byref(handle))
        else:
            app = structure(Application)
            code = self.call(0xEEE566B2, [HANDLE, C.c_wchar_p, C.POINTER(HANDLE), C.POINTER(Application)],
                             self.session, executable, C.byref(handle), C.byref(app), allow=(-166,))
            if code == -166:
                if not create:
                    return None, {'name': 'RebooterX · ' + executable, 'apps': 1, 'new': True}
                info = structure(Profile)
                info.name = 'RebooterX · ' + executable + ' · ' + uuid.uuid4().hex[:8]
                self.call(0xCC176068, [HANDLE, C.POINTER(Profile), C.POINTER(HANDLE)],
                          self.session, C.byref(info), C.byref(handle))
                app.name, app.friendly = executable, executable
                self.call(0x4347A9DE, [HANDLE, HANDLE, C.POINTER(Application)],
                          self.session, handle, C.byref(app))
        info = structure(Profile)
        self.call(0x61CD6FD6, [HANDLE, HANDLE, C.POINTER(Profile)], self.session, handle, C.byref(info))
        return handle, {'name': info.name, 'apps': info.apps, 'new': False}

    def named_profile(self, name):
        handle = HANDLE()
        self.call(0x7E4A9A0B, [HANDLE, C.c_wchar_p, C.POINTER(HANDLE)],
                  self.session, name, C.byref(handle))
        return handle

    def get(self, profile, identifier):
        if profile is None:
            return {'value': None, 'explicit': False}
        setting = structure(Setting)
        code = self.call(0x73BF8338, [HANDLE, HANDLE, U32, C.POINTER(Setting)],
                         self.session, profile, identifier, C.byref(setting), allow=(-160,))
        if code == -160:
            return {'value': None, 'explicit': False}
        if setting.type != 0:
            raise NvError('Expected a DWORD driver setting.')
        return {'value': setting.current.dword,
                'explicit': setting.location == 0 and not setting.predefined}

    def set(self, profile, identifier, value):
        if not value['explicit']:
            self.call(0xE4A26362, [HANDLE, HANDLE, U32], self.session, profile, identifier, allow=(-160,))
            return
        setting = structure(Setting)
        setting.id, setting.type, setting.current.dword = identifier, 0, value['value']
        self.call(0x577DD202, [HANDLE, HANDLE, C.POINTER(Setting)],
                  self.session, profile, C.byref(setting))

    def save(self):
        self.call(0xFCBC7E14, [HANDLE], self.session)


def executable_name(path):
    if not path:
        return None
    candidate = Path(path)
    if candidate.suffix.lower() != '.exe' or not candidate.is_file():
        raise NvError('Select an existing game .exe first.')
    return candidate.name.lower()


class Profiles:
    def __init__(self, folder, driver=Driver):
        self.folder, self.driver = Path(folder), driver

    def plan(self, path, choices):
        executable = executable_name(path)
        if not choices:
            raise NvError('Select at least one setting.')
        for identifier, value in choices.items():
            if identifier not in OPTIONS or value not in OPTIONS[identifier].values():
                raise NvError('Unsupported setting or value.')
        with self.driver() as driver:
            game, info = driver.profile(executable)
            base, base_info = driver.profile()
            changes = []
            for identifier, value in choices.items():
                global_setting = identifier == CACHE or executable is None
                handle = base if global_setting else game
                meta = base_info if global_setting else info
                changes.append({'id': identifier, 'profile': meta['name'],
                                'global': global_setting, 'new': meta['new'],
                                'before': driver.get(handle, identifier),
                                'after': {'value': value, 'explicit': True}})
            return {'schema': 1, 'executable': executable, 'profile': info,
                    'changes': changes, 'status': 'preview'}

    def apply(self, plan):
        with self.driver() as driver:
            game, info = driver.profile(plan['executable'])
            # Revalidate the preview before creating profiles or committing anything.
            if info != plan['profile']:
                raise NvError('Profile changed. Read settings again before applying.')
            handles = {}
            for change in plan['changes']:
                handle = driver.named_profile(change['profile']) if not change['new'] else game
                if driver.get(handle, change['id']) != change['before']:
                    raise NvError('Driver settings changed after preview. Read them again.')
                handles[change['id']] = handle
            if any(c['new'] for c in plan['changes']):
                game, info = driver.profile(plan['executable'], create=True)
                for change in plan['changes']:
                    if change['new']:
                        change['profile'] = info['name']
                        handles[change['id']] = game
            receipt = {**plan, 'status': 'pending', 'time': time.strftime('%Y-%m-%d %H:%M:%S')}
            filename = self.folder / (f'{time.time_ns():020d}-' + uuid.uuid4().hex[:8] + '.json')
            self.write(filename, receipt)  # Backup must succeed before SaveSettings.
            try:
                for change in receipt['changes']:
                    driver.set(handles[change['id']], change['id'], change['after'])
            except Exception:
                receipt['status'] = 'aborted'  # No SaveSettings: session changes are discarded.
                self.write(filename, receipt)
                raise
            driver.save()
        with self.driver() as driver:
            for change in receipt['changes']:
                if driver.get(driver.named_profile(change['profile']), change['id']) != change['after']:
                    raise NvError(f'Saved value could not be verified. Backup: {filename}')
        receipt['status'] = 'applied'
        self.write(filename, receipt)
        return filename

    @staticmethod
    def write(path, value):
        atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2).encode('utf-8'))

    def latest(self):
        for path in sorted(self.folder.glob('*.json'), reverse=True):
            receipt = json.loads(path.read_text(encoding='utf-8'))
            if receipt.get('status') in ('applied', 'pending'):
                return path, receipt
        raise NvError('No NVIDIA backup is available.')

    def restore(self, expected_path=None):
        path, receipt = self.latest()
        if expected_path is not None and path != expected_path:
            raise NvError('The latest backup changed. Review it again before restoring.')
        with self.driver() as driver:
            handles = {}
            for change in receipt['changes']:
                handle = driver.named_profile(change['profile'])
                if driver.get(handle, change['id']) != change['after']:
                    raise NvError('Driver settings changed since this backup. Automatic restore stopped.')
                handles[change['id']] = handle
            for change in receipt['changes']:
                driver.set(handles[change['id']], change['id'], change['before'])
            driver.save()
        with self.driver() as driver:
            for change in receipt['changes']:
                actual = driver.get(driver.named_profile(change['profile']), change['id'])
                before = change['before']
                if (before['explicit'] and actual != before) or (not before['explicit'] and actual['explicit']):
                    raise NvError('Restore verification failed. Backup retained.')
        receipt['status'] = 'restored'
        self.write(path, receipt)
        return path


def describe(identifier, state):
    label = next((k for k, v in OPTIONS[identifier].items() if v == state['value']),
                 'Driver default' if state['value'] is None else hex(state['value']))
    return label + ('' if state['explicit'] else ' [inherited / default]')
