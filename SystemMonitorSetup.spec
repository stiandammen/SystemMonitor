# -*- mode: python ; coding: utf-8 -*-
import sys
import os

# --------------------------------------------------------------------------
# Same PyInstaller/Windows isolated-import workaround as SystemMonitor.spec
# (see that file for the full write-up). This installer also touches
# win32com (win32com.client.Dispatch, for shortcut creation), so it's
# subject to the same risk - skip our own systemmonitor.* package from
# PyInstaller's DLL-search-path probe, which is a no-op for us anyway since
# none of our code calls os.add_dll_directory() or touches PATH.
# --------------------------------------------------------------------------
if sys.platform == 'win32':
    import PyInstaller.building.build_main as _pyi_build_main

    _original_find_binary_dependencies = _pyi_build_main.find_binary_dependencies

    def _find_binary_dependencies_skip_own_package(binaries, import_packages, symlink_suppression_patterns):
        filtered = [
            pkg for pkg in import_packages
            if pkg != 'systemmonitor' and not pkg.startswith('systemmonitor.')
        ]
        return _original_find_binary_dependencies(binaries, filtered, symlink_suppression_patterns)

    _pyi_build_main.find_binary_dependencies = _find_binary_dependencies_skip_own_package

base_dir = os.getcwd()
src_dir = os.path.join(base_dir, 'src')

# This installer embeds a copy of the already-built SystemMonitor.exe and
# copies it out to the user's chosen install folder at runtime (see
# InstallWorker in setup_installer.py, which looks for "SystemMonitor.exe"
# and "icon.png" next to itself via sys._MEIPASS). This spec therefore MUST
# be built AFTER "pyinstaller SystemMonitor.spec" has produced dist/SystemMonitor.exe
# (see .github/workflows/release.yml step ordering).
main_exe_path = os.path.join(base_dir, 'dist', 'SystemMonitor.exe')
icon_png_path = os.path.join(src_dir, 'systemmonitor', 'assets', 'icon.png')

datas = []
if os.path.exists(main_exe_path):
    datas.append((main_exe_path, '.'))
if os.path.exists(icon_png_path):
    datas.append((icon_png_path, '.'))

binaries = []
hiddenimports = [
    'win32com',
    'win32com.client',
    'win32com.client.util',
    'win32timezone',   # common PyInstaller+pywin32 gotcha if omitted
    'pythoncom',
    'pywintypes',
    'winreg',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
]

a = Analysis(
    ['setup_main.py'],
    pathex=[base_dir, src_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SystemMonitorSetup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=False,
    icon=os.path.join(src_dir, 'systemmonitor', 'assets', 'icon.ico') if os.path.exists(os.path.join(src_dir, 'systemmonitor', 'assets', 'icon.ico')) else None,
)
