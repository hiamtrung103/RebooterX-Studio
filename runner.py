"""Elevated console host. Uses unmodified official CLI and records each package."""
import argparse
import ctypes
from ctypes import wintypes
import json
import msvcrt
from pathlib import Path
import shutil
import os
import re
import subprocess
import time

import core
from execution import now, outcome
import rollback


def release_final_prompt():
    """Send Return only to this host's own inherited console, after CLI 'Exiting.'."""
    class Key(ctypes.Structure):
        _fields_ = [('down', wintypes.BOOL), ('repeat', wintypes.WORD), ('virtual', wintypes.WORD),
                    ('scan', wintypes.WORD), ('char', wintypes.WCHAR), ('control', wintypes.DWORD)]
    class Event(ctypes.Union):
        _fields_ = [('key', Key), ('padding', ctypes.c_byte*16)]
    class Input(ctypes.Structure):
        _fields_ = [('type', wintypes.WORD), ('event', Event)]
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.GetStdHandle.argtypes = [wintypes.DWORD]
    api.GetStdHandle.restype = wintypes.HANDLE
    api.WriteConsoleInputW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Input), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    api.WriteConsoleInputW.restype = wintypes.BOOL
    events = (Input*2)()
    for i in range(2):
        events[i].type = 1
        events[i].event.key = Key(i == 0, 1, 13, 28, '\r', 0)
    written = wintypes.DWORD()
    if not api.WriteConsoleInputW(api.GetStdHandle(-10 & 0xffffffff), events, 2, ctypes.byref(written)):
        raise ctypes.WinError(ctypes.get_last_error())


def read_logs(folder):
    return '\n'.join(path.read_text(encoding='utf-8-sig', errors='replace')
                     for path in sorted(folder.glob('optimizerNXT-logs/*.log')))


def execute(executable, yaml_path, engine):
    engine.mkdir(parents=True)
    local_exe = engine / 'optimizerNXT.exe'
    shutil.copy2(executable, local_exe)
    with subprocess.Popen([str(local_exe), 'apply', str(yaml_path)], cwd=engine) as process:
        released = False
        while process.poll() is None:
            text = read_logs(engine)
            if not released and (re.search(r'^\[[^\]]+\] \[INFO\]: Exiting\.\s*$', text, re.M) or
                                 'Another instance of ' in text):
                release_final_prompt()
                released = True
            time.sleep(.15)
        return process.returncode, read_logs(engine)


def write_report(folder, report):
    core.atomic_write(folder / 'run-result.json', json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8'))


def apply(args):
    packages = json.loads((args.folder / 'selection.json').read_text(encoding='utf-8'))['packages']
    report = {'results': {}, 'complete': False, 'pid': os.getpid()}
    write_report(args.folder, report)
    any_error = False
    for index, package in enumerate(packages):
        name = package['name']
        if Path(name).name != name or not name.endswith(('.yaml', '.yml')):
            raise ValueError('Invalid package name.')
        result = {**package, 'status': 'failed', 'time': now(), 'folder': str(args.folder), 'undo': None}
        undo = None
        try:
            content = (args.folder / name).read_bytes()
            if core.git_hash(content) != package['sha'] or core.git_hash((args.folder / (name+'.sig')).read_bytes()) != package['sig_sha']:
                raise ValueError('Package checksum mismatch before execution.')
            try:
                undo = rollback.capture(content, args.folder / 'rollback' / str(index))
            except Exception as error:
                result['undo_note'] = str(error)
            code, log = execute(args.exe, args.folder / name, args.folder / 'engine' / str(index))
            result.update(status=outcome(code, log), code=code, time=now())
            core.atomic_write(args.folder / f'{name}.log', log.encode('utf-8'))
            if undo:
                try:
                    rollback.seal(undo)
                    result['undo'] = str(undo)
                except Exception as error:
                    result['undo_note'] = str(error)
            any_error |= result['status'] != 'applied'
        except Exception as error:
            result['error'] = str(error)
            any_error = True
        report['results'][name] = result
        write_report(args.folder, report)
    report['complete'] = True
    write_report(args.folder, report)
    return 1 if any_error else 0


def undo(args):
    result = json.loads((args.folder / 'restore-source.json').read_text(encoding='utf-8'))
    result['restores_folder'] = result.get('restores_folder', result['folder'])
    result['folder'] = str(args.folder)
    result['status'] = 'running'
    report = {'results': {args.package: result}, 'complete': False, 'pid': os.getpid()}
    write_report(args.folder, report)
    try:
        rollback.restore(Path(result['undo']))
        result.update(status='restored', time=now())
        result.pop('error', None)
        code = 0
    except Exception as error:
        result.update(status='restore_failed', error=str(error), time=now())
        code = 1
    report['complete'] = True
    write_report(args.folder, report)
    return code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exe', type=Path)
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--sid', required=True)
    parser.add_argument('--auto-close', action='store_true')
    parser.add_argument('--package')
    args = parser.parse_args()
    try:
        if rollback.user_sid() != args.sid:
            raise ValueError('Use administrator approval for the same Windows user. / Cần cấp quyền cho cùng tài khoản Windows.')
        code = undo(args) if args.package else apply(args)
    except Exception as error:
        print(error, flush=True)
        core.atomic_write(args.folder / 'runner-error.txt', str(error).encode('utf-8'))
        code = 1
    print('\nFinished. See RebooterX Studio for per-package results. / Xem ket qua tung goi trong RebooterX Studio.', flush=True)
    if not args.auto_close:
        print('Press any key to close / Nhan phim bat ky de dong...', flush=True)
        msvcrt.getwch()
    return code


if __name__ == '__main__':
    raise SystemExit(main())
