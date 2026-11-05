"""Administrator-only startup and frozen console dispatch."""
import ctypes
import os
from pathlib import Path
import subprocess
import sys


def is_admin():
    return os.name == 'nt' and bool(ctypes.windll.shell32.IsUserAnAdmin())


def ensure_admin():
    """None means continue; an integer is the launcher's exit status."""
    if is_admin():
        return None
    if os.name != 'nt':
        return 1
    # The packaged EXE's requireAdministrator manifest requests UAC before Python
    # starts. Keep the runtime check too, and elevate source launches explicitly.
    if getattr(sys, 'frozen', False):
        return 1
    shell = ctypes.WinDLL('shell32', use_last_error=True)
    shell.ShellExecuteW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p,
                                  ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_int]
    shell.ShellExecuteW.restype = ctypes.c_void_p
    code = shell.ShellExecuteW(None, 'runas', sys.executable,
                              subprocess.list2cmdline([str(Path(sys.argv[0]).resolve()), *sys.argv[1:]]),
                              str(Path(sys.argv[0]).resolve().parent), 1)
    return 0 if code and code > 32 else 1


def attach_runner_console():
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    if not api.GetConsoleWindow() and not api.AllocConsole():
        raise ctypes.WinError(ctypes.get_last_error())
    sys.stdin = open('CONIN$', 'r', encoding='utf-8')
    sys.stdout = open('CONOUT$', 'w', encoding='utf-8', buffering=1)
    sys.stderr = open('CONOUT$', 'w', encoding='utf-8', buffering=1)


def dispatch_runner():
    sys.argv.remove('--runner')
    if getattr(sys, 'frozen', False):
        attach_runner_console()
    import runner
    return runner.main()


def self_test(report_path):
    """Read/import/UI smoke test. Never applies Windows or NVIDIA tweaks."""
    import json
    import tempfile
    import core
    import rollback
    import runner
    import nvidia
    from ui import StudioApp
    from theme import ICON_DIR
    from catalog import PACKAGES
    errors = []
    with tempfile.TemporaryDirectory(prefix='rebooterx-smoke-') as folder:
        app = StudioApp(Path(folder), autoload=False)
        app.attributes('-alpha', 0)
        app.report_callback_exception = lambda *args: errors.append(str(args))
        app.packages = [{'name': name + '.yaml', 'path': name, 'sha': 'b'*40,
                         'sig_sha': 'c'*40, 'revision': 'a'*40} for name in PACKAGES]
        app.render()
        for key in ('windows_nav', 'nvidia', 'tools', 'activity', 'settings'):
            app.navigate(key)
            app.update()
        app.nvidia_page.preset()
        assert len(app.nvidia_page.values) == len(nvidia.OPTIONS)
        for language in ('English', 'Tiếng Việt'):
            app.change_language(language)
            app.update()
        assert not errors, errors
        report = {'ok': True, 'admin': is_admin(), 'frozen': bool(getattr(sys, 'frozen', False)),
                  'data': str(core.DATA), 'icons': len(list(ICON_DIR.glob('*.png'))),
                  'nvidia_options': len(nvidia.OPTIONS), 'pages': list(app.nav), 'errors': errors}
        for job in app.tk.call('after', 'info'):
            app.tk.call('after', 'cancel', job)
        app.destroy()
    core.atomic_write(Path(report_path), json.dumps(report, indent=2).encode('utf-8'))
    return 0


def network_test(report_path):
    """Verify real HTTPS/redirects/hashes in the frozen build; never run downloads."""
    import json
    import tempfile
    import certifi
    import core
    from network import tls_context
    context = tls_context()
    results = []
    with tempfile.TemporaryDirectory(prefix='rebooterx-network-') as directory:
        repo = core.Repository(Path(directory))
        checks = [
            ('GitHub API', lambda: len(repo.request(core.API))),
            ('GitHub raw content', lambda: len(repo.request('https://raw.githubusercontent.com/hellzerg/optimizerNXT/main/README.md'))),
            ('Official CLI download + SHA-256 (not executed)', lambda: repo.download_cli().stat().st_size),
        ]
        for name, operation in checks:
            try:
                results.append({'check': name, 'ok': True, 'bytes': operation()})
            except Exception as error:
                results.append({'check': name, 'ok': False, 'error': str(error)})
    success = all(result['ok'] for result in results)
    report = {'ok': success, 'admin': is_admin(), 'frozen': bool(getattr(sys, 'frozen', False)),
              'ca_bundle_present': Path(certifi.where()).is_file(),
              'verify_mode': int(context.verify_mode), 'check_hostname': context.check_hostname,
              'results': results}
    core.atomic_write(Path(report_path), json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8'))
    return 0 if success else 1
