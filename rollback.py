"""Conservative rollback of complete, existing registry subtrees only."""
import base64
import hashlib
import json
from pathlib import Path
import winreg

import win32api
import win32con
import win32security
import yaml

import core

HIVES = {'HKCU': winreg.HKEY_CURRENT_USER, 'HKLM': winreg.HKEY_LOCAL_MACHINE}
SECURITY = (win32security.OWNER_SECURITY_INFORMATION | win32security.GROUP_SECURITY_INFORMATION |
            win32security.DACL_SECURITY_INFORMATION)


def user_sid():
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
    try:
        sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
    finally:
        token.Close()
    return win32security.ConvertSidToStringSid(sid)


def privileges():
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(),
            win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY)
    try:
        changes = [(win32security.LookupPrivilegeValue(None, name), win32con.SE_PRIVILEGE_ENABLED)
                   for name in ('SeBackupPrivilege', 'SeRestorePrivilege')]
        win32security.AdjustTokenPrivileges(token, False, changes)
    finally:
        token.Close()


def registry_plan(content):
    stage = yaml.safe_load(content)
    if not isinstance(stage, dict) or set(stage) != {'jobs'} or not isinstance(stage['jobs'], list):
        return None
    paths = set()
    for job in stage['jobs']:
        if not isinstance(job, dict) or set(job) - {'name', 'description', 'condition', 'steps'}:
            return None
        for step in job.get('steps', []):
            if not isinstance(step, dict) or set(step) - {'name', 'condition', 'registry'} or 'registry' not in step:
                return None
            registry = step['registry']
            if not isinstance(registry, dict) or set(registry) != {'entries'}:
                return None
            for entry in registry['entries']:
                if not isinstance(entry, dict) or set(entry) - {'hive', 'path', 'add', 'delete'}:
                    return None
                hive = {'HKEY_LOCAL_MACHINE': 'HKLM', 'HKEY_CURRENT_USER': 'HKCU'}.get(entry.get('hive'), entry.get('hive'))
                path = entry.get('path', '').strip('\\')
                # Never offer an entire hive, a merged HKCR view, or arbitrary script undo.
                if hive not in HIVES or not path or '\\' not in path or any(p in ('', '.', '..') for p in path.split('\\')):
                    return None
                paths.add((hive, path))
    if not paths:
        return None
    return [(hive, path) for hive, path in sorted(paths)
            if not any(hive == h and path.lower().startswith(p.lower()+'\\') for h, p in paths if (h, p) != (hive, path))]


def encoded(value):
    return {'bytes': base64.b64encode(value).decode('ascii')} if isinstance(value, bytes) else value


def fingerprint(hive, path):
    count = 0
    def visit(key):
        nonlocal count
        count += 1
        if count > 4096:
            raise ValueError('Registry subtree is too large for automatic rollback.')
        subkeys, values, _ = winreg.QueryInfoKey(key)
        descriptor = win32security.GetSecurityInfo(int(key), win32security.SE_REGISTRY_KEY, SECURITY)
        sddl = win32security.ConvertSecurityDescriptorToStringSecurityDescriptor(descriptor, 1, SECURITY)
        data = sorted([(name, kind, encoded(value)) for name, value, kind in
                       (winreg.EnumValue(key, i) for i in range(values))], key=lambda row: row[0].casefold())
        children = []
        for name in sorted((winreg.EnumKey(key, i) for i in range(subkeys)), key=str.casefold):
            with winreg.OpenKey(key, name, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as child:
                children.append((name, visit(child)))
        return sddl, data, children
    with winreg.OpenKey(HIVES[hive], path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
        data = visit(key)
    return hashlib.sha256(json.dumps(data, ensure_ascii=True, sort_keys=True).encode()).hexdigest()


def save_manifest(path, value):
    core.atomic_write(path, json.dumps(value, indent=2).encode('utf-8'))


def capture(content, folder):
    plan = registry_plan(content)
    if plan is None:
        return None
    privileges()
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {'sid': user_sid(), 'roots': [], 'ready': False}
    for index, (hive, path) in enumerate(plan):
        before = fingerprint(hive, path)  # Missing/inaccessible keys disable rollback, never guessed.
        backup = folder / f'{index}.hiv'
        with winreg.OpenKey(HIVES[hive], path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            win32api.RegSaveKey(int(key), str(backup), None)
        if fingerprint(hive, path) != before:
            raise ValueError('Registry changed while taking the rollback snapshot.')
        manifest['roots'].append({'hive': hive, 'path': path, 'before': before, 'backup': backup.name,
            'sha256': hashlib.sha256(backup.read_bytes()).hexdigest(), 'restored': False})
    save_manifest(folder / 'undo.json', manifest)
    return folder / 'undo.json'


def seal(path):
    value = json.loads(path.read_text(encoding='utf-8'))
    for root in value['roots']:
        root['after'] = fingerprint(root['hive'], root['path'])
    value['ready'] = True
    save_manifest(path, value)


def restore(path):
    value = json.loads(path.read_text(encoding='utf-8'))
    if not value.get('ready') or value['sid'] != user_sid():
        raise ValueError('Rollback snapshot is unavailable or belongs to another Windows user.')
    privileges()
    remaining = [root for root in value['roots'] if not root['restored']]
    # Validate every subtree before the first write; later user/driver changes block undo.
    for root in remaining:
        if Path(root['backup']).name != root['backup']:
            raise ValueError('Invalid backup filename.')
        backup = path.parent / root['backup']
        if hashlib.sha256(backup.read_bytes()).hexdigest() != root['sha256']:
            raise ValueError('Rollback backup checksum mismatch.')
        if fingerprint(root['hive'], root['path']) != root['after']:
            raise ValueError('Settings changed after this run. Automatic rollback was blocked to preserve newer changes. / Thiết lập đã đổi sau lần chạy; không ghi đè thay đổi mới.')
    for root in remaining:
        if fingerprint(root['hive'], root['path']) != root['after']:
            raise ValueError('Settings changed during rollback. Remaining subtrees were not restored.')
        with winreg.OpenKey(HIVES[root['hive']], root['path'], 0,
                            winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY) as key:
            # No REG_FORCE_RESTORE: Windows can refuse a subtree that is in active use.
            win32api.RegRestoreKey(int(key), str(path.parent / root['backup']), 0)
        if fingerprint(root['hive'], root['path']) != root['before']:
            raise ValueError('Restored registry did not match its original snapshot.')
        root['restored'] = True
        save_manifest(path, value)
