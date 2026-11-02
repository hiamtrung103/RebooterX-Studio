# Build on 64-bit Windows: python -m PyInstaller --noconfirm RebooterX-Studio.spec
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

datas = [('assets', 'assets'), ('LICENSE', '.'), ('README.md', '.')]
datas += collect_data_files('customtkinter')
for package in ('customtkinter', 'Pillow', 'PyYAML', 'pywin32'):
    datas += copy_metadata(package)
a = Analysis(['app.py'], pathex=[], binaries=[], datas=datas,
             hiddenimports=['runner', 'bootstrap', 'nvidia_ui', 'win32security', 'win32event'],
             hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='RebooterX-Studio',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False, argv_emulation=False,
          target_arch=None, codesign_identity=None, entitlements_file=None,
          uac_admin=True, version='windows_version.txt')
