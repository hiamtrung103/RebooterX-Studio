"""Official Mem Reduct downloads, verified portable installation and RAM status."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile

import core

PROJECT = 'https://github.com/henrypp/memreduct'
API = 'https://api.github.com/repos/henrypp/memreduct'


def architecture():
    machine = (os.environ.get('PROCESSOR_ARCHITEW6432') or platform.machine()).lower()
    return 'arm64' if 'arm' in machine else '64' if '64' in machine else '32'


def manifest_hash(manifest, filename, section=None):
    current = None
    for line in manifest.splitlines():
        if line.startswith('#'):
            current = line.lower().replace('-', '').replace(' ', '')
        match = re.fullmatch(r'([a-fA-F0-9]{64})\s+\*?(.+)', line.strip())
        if match and match[2] == filename and (section is None or current == '#' + section + ('bit' if section != 'arm64' else '')):
            return match[1].lower()
    raise ValueError('Official SHA-256 manifest has no matching entry: ' + filename)


def check_hash(content, expected):
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError('Mem Reduct SHA-256 verification failed.')


def seven_zip():
    candidates = [shutil.which('7z'), shutil.which('7za')]
    for variable in ('ProgramFiles', 'ProgramFiles(x86)'):
        if os.environ.get(variable):
            candidates.append(str(Path(os.environ[variable]) / '7-Zip' / '7z.exe'))
    return next((p for p in candidates if p and Path(p).is_file()), None)


class MemReduct:
    def __init__(self, data=core.DATA):
        self.folder = Path(data) / 'tools' / 'memreduct'
        self.repo = core.Repository(Path(data))

    def installed(self):
        try:
            receipt = json.loads((self.folder / 'verified.json').read_text(encoding='utf-8'))
            path = self.folder / 'memreduct.exe'
            check_hash(path.read_bytes(), receipt['sha256'])
            return path
        except (OSError, ValueError, KeyError):
            return None

    def install(self):
        extractor = seven_zip()
        if not extractor:
            raise RuntimeError('Install 7-Zip from https://www.7-zip.org then retry. / Cài 7-Zip rồi thử lại.')
        release = json.loads(self.repo.request(API + '/releases/latest'))
        assets = release.get('assets', [])
        archive = next((a for a in assets if a['name'].endswith('-bin.7z')), None)
        checksum = next((a for a in assets if a['name'].endswith('.sha256')), None)
        if not archive or not checksum:
            raise ValueError('Official Mem Reduct release is missing its portable archive or SHA-256 manifest.')
        def fetch(asset):
            url = asset['browser_download_url']
            if not url.startswith(PROJECT + '/releases/download/'):
                raise ValueError('Unexpected Mem Reduct release URL.')
            return self.repo.request(url)
        manifest = fetch(checksum).decode('utf-8-sig')
        content = fetch(archive)
        check_hash(content, manifest_hash(manifest, archive['name']))
        arch = architecture()
        executable_hash = manifest_hash(manifest, 'memreduct.exe', arch)
        names = ['memreduct.exe', 'memreduct.exe.sig', 'memreduct.lng', 'portable.dat', 'License.txt', 'Readme.txt', 'History.txt']
        with tempfile.TemporaryDirectory(prefix='rebooterx-mem-') as temporary:
            root = Path(temporary)
            packed = root / 'official.7z'
            packed.write_bytes(content)
            destination = root / 'extracted'
            subprocess.run([extractor, 'e', str(packed), '-o' + str(destination), '-y',
                            *['memreduct/' + arch + '/' + name for name in names]],
                           check=True, capture_output=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            check_hash((destination / 'memreduct.exe').read_bytes(), executable_hash)
            for name in names:
                source = destination / name
                if source.is_symlink() or not source.is_file():
                    raise ValueError('Invalid portable archive entry: ' + name)
                core.atomic_write(self.folder / name, source.read_bytes())
        core.atomic_write(self.folder / 'verified.json', json.dumps({
            'version': release['tag_name'], 'architecture': arch, 'sha256': executable_hash,
            'source': archive['browser_download_url'],
        }, indent=2).encode('utf-8'))
        return self.folder / 'memreduct.exe'

    def launch(self, clean=None):
        executable = self.installed()
        if not executable:
            raise ValueError('Download and verify Mem Reduct first. / Hãy tải và xác minh Mem Reduct trước.')
        if clean not in (None, 'default', 'full'):
            raise ValueError('Invalid cleanup mode.')
        args = [] if clean is None else ['-clean:full' if clean == 'full' else '-clean']
        return core.run_program(executable, args, self.folder, wait=clean is not None)


def ram_status():
    if os.name != 'nt':
        return None
    class Status(ctypes.Structure):
        _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong),
                    *[(name, ctypes.c_ulonglong) for name in ('total', 'available', 'page_total',
                       'page_available', 'virtual_total', 'virtual_available', 'extended')]]
    status = Status()
    status.length = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise ctypes.WinError()
    return status.total, status.available, status.load
