"""Persistent evidence of executions, distinct from current Windows state."""
from datetime import datetime
import json
import os
from pathlib import Path
import re
import threading

import core


def now():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def outcome(code, text):
    messages = re.findall(r'^\[\d{4}-\d\d-\d\d [^\]]+\] \[(INFO|WARN|ERROR)\]: (.*)$', text, re.M)
    infos = [message for level, message in messages if level == 'INFO']
    if code != 0 or any(level == 'ERROR' for level, _ in messages):
        return 'failed'
    if any(level == 'WARN' for level, _ in messages):
        return 'uncertain'
    if any(message.startswith('Skipping ') for message in infos):
        return 'skipped'
    if ('Verified 1/1 YAML files.' in infos and 'Exiting.' in infos and
            any(message.startswith('Executing step: ') for message in infos) and
            any(message.startswith('Finished executing YAML stage: ') for message in infos)):
        return 'applied'
    return 'uncertain'


def process_alive(pid):
    import win32api
    import win32event
    try:
        handle = win32api.OpenProcess(0x100000, False, pid)
        try:
            return win32event.WaitForSingleObject(handle, 0) == win32event.WAIT_TIMEOUT
        finally:
            handle.Close()
    except Exception as error:
        return getattr(error, 'winerror', None) == 5


class History:
    def __init__(self, data):
        self.path = Path(data) / 'history.json'
        self.lock = threading.RLock()
        try:
            value = json.loads(self.path.read_text(encoding='utf-8'))
            if value.get('version') != 1 or not isinstance(value.get('packages'), dict) or not isinstance(value.get('pending'), dict):
                raise ValueError('Invalid local history.')
            self.value = value
        except (OSError, ValueError, AttributeError):
            self.value = {'version': 1, 'packages': {}, 'pending': {}}
        self.recover()

    def save(self):
        core.atomic_write(self.path, json.dumps(self.value, ensure_ascii=False, indent=2).encode('utf-8'))

    def begin(self, folder, packages):
        with self.lock:
            self.value['pending'][str(folder)] = {'packages': packages, 'owner_pid': os.getpid()}
            for package in packages:
                item = self.value['packages'].setdefault(package['name'], {})
                item['last'] = {**package, 'status': 'running', 'time': now(), 'folder': str(folder)}
            self.save()

    def recover(self):
        changed = False
        with self.lock:
            for folder, pending in list(self.value['pending'].items()):
                packages = pending if isinstance(pending, list) else pending['packages']
                owner = None if isinstance(pending, list) else pending.get('owner_pid')
                try:
                    report = json.loads((Path(folder) / 'run-result.json').read_text(encoding='utf-8'))
                    expected = {p['name']: p for p in packages}
                    accepted = set()
                    for name, result in report.get('results', {}).items():
                        if (name not in expected or not isinstance(result, dict) or
                            result.get('sha') != expected[name]['sha'] or result.get('name') != name or
                            result.get('folder') != folder or result.get('status') not in
                            ('applied', 'failed', 'uncertain', 'skipped', 'running', 'restored', 'restore_failed')):
                            continue
                        accepted.add(name)
                        item = self.value['packages'].setdefault(name, {})
                        if item.get('last') == result:
                            continue
                        item['last'] = result
                        if result['status'] == 'applied':
                            if (item.get('applied') or {}).get('folder') != result['folder']:
                                previous = item.get('applied')
                                item['applied'] = {**result, **({'_previous': previous} if previous else {})}
                        elif result['status'] == 'restored':
                            applied = item.get('applied') or {}
                            if applied.get('folder') == result.get('restores_folder', result['folder']):
                                item['applied'] = applied.get('_previous')
                        changed = True
                    if report.get('complete'):
                        for name in set(expected) - accepted:
                            self.value['packages'][name]['last'].update(status='uncertain', time=now())
                        self.value['pending'].pop(folder)
                        changed = True
                    elif report.get('pid') and not process_alive(report['pid']):
                        for name, package in expected.items():
                            if name not in report.get('results', {}):
                                self.value['packages'][name]['last'].update(status='uncertain', time=now())
                        self.value['pending'].pop(folder)
                        changed = True
                except (OSError, ValueError, KeyError, TypeError, AttributeError):
                    if owner and not process_alive(owner):
                        for package in packages:
                            self.value['packages'][package['name']]['last'].update(status='uncertain', time=now())
                        self.value['pending'].pop(folder)
                        changed = True
            if changed:
                self.save()
        return changed

    def item(self, name):
        with self.lock:
            return dict(self.value['packages'].get(name, {}))

    def finish(self, folder, error=None):
        self.recover()
        if error is None:
            try:
                error = (Path(folder) / 'runner-error.txt').read_text(encoding='utf-8')
            except OSError:
                pass
        with self.lock:
            pending = self.value['pending'].pop(str(folder), [])
            packages = pending if isinstance(pending, list) else pending['packages']
            for package in packages:
                last = self.value['packages'][package['name']]['last']
                if last['status'] == 'running':
                    last.update(status='uncertain', error=error or 'No complete per-package result was recorded.')
            self.save()

    def status(self, package):
        item = self.item(package['name'])
        last = item.get('last') or {}
        applied = item.get('applied') or {}
        if last.get('status') in ('failed', 'uncertain', 'skipped', 'running', 'restore_failed'):
            return last['status']
        if applied:
            return 'applied' if applied['sha'] == package['sha'] else 'older'
        return last.get('status', 'never')

    def undo(self, name):
        item = self.item(name)
        last = item.get('last') or {}
        if last.get('status') == 'restored':
            last = item.get('applied') or {}
        path = Path(last.get('undo', ''))
        return path if last.get('status') != 'running' and path.is_file() else None
