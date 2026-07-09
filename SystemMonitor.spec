# -*- mode: python ; coding: utf-8 -*-
import sys
import os

# --------------------------------------------------------------------------
# Work around a known PyInstaller/Windows bug: on Windows, PyInstaller
# isolated-imports every collected pure-Python package in a single shared
# child interpreter to detect os.add_dll_directory()/PATH side effects
# (see PyInstaller.building.build_main.find_binary_dependencies). Certain
# import orders corrupt that child interpreter and crash it with
# STATUS_STACK_OVERFLOW (exit code 3221225725) on a *later*, unrelated
# import - PyInstaller itself works around this for known offenders like
# 'pyqtgraph.canvas' and 'PySimpleGUI' (see their build_main.py, and
# https://github.com/pyinstaller/pyinstaller/issues/8322). Our own build hit
# the exact same crash signature while importing 'systemmonitor.data'.
#
# None of our first-party systemmonitor.* modules call
# os.add_dll_directory() or touch PATH (verified by grep), so this DLL
# search-path probe is a no-op for them anyway. We therefore skip the whole
# systemmonitor.* namespace from that probe, the same way PyInstaller
# already skips the packages named above.
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
# --------------------------------------------------------------------------

# Base directory
base_dir = os.getcwd()
src_dir = os.path.join(base_dir, 'src')

# NOTE: we deliberately do NOT use collect_all('systemmonitor') here.
# collect_all() is meant for THIRD-PARTY packages that need their data
# files/hidden imports discovered automatically - using it on our own
# first-party source package forces PyInstaller to isolated-import-walk
# every single submodule individually (including unused/dead ones), which
# is unnecessary (PyInstaller's normal static analysis of __main__.py
# already finds everything we actually import) and was the likely cause
# of a STATUS_STACK_OVERFLOW crash in PyInstaller's isolated subprocess
# during the GitHub Actions build. It would also have bundled the local
# src/systemmonitor/logs/*.log files, which should never ship at all.
datas = []
binaries = []
hiddenimports = []

# Explicitly add standard library modules that are failing or commonly needed
hiddenimports += [
    'csv',
    '_csv',
    'json',
    '_json',
    'datetime',
    'logging',
    'pathlib',
    'enum',
    'typing',
    'inspect',
    're',
    'struct',
    'threading',
    'psutil',
    'wmi',
    'GPUtil',
    'qtawesome',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
]

# Add assets
assets_src = os.path.join(src_dir, 'systemmonitor', 'assets')
if os.path.exists(assets_src):
    datas += [(assets_src, 'systemmonitor/assets')]

a = Analysis(
    ['__main__.py'],
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
    name='SystemMonitor',
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
    uac_admin=True,
    icon=os.path.join(src_dir, 'systemmonitor', 'assets', 'hacker.png') if os.path.exists(os.path.join(src_dir, 'systemmonitor', 'assets', 'hacker.png')) else None,
)
