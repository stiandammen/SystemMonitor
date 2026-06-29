# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all

# Base directory
base_dir = os.getcwd()
src_dir = os.path.join(base_dir, 'src')
python_lib = r'C:\Users\RSman\AppData\Local\Python\pythoncore-3.14-64\Lib'
site_packages = r'C:\Users\RSman\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages'

# Collect everything from systemmonitor
datas, binaries, hiddenimports = collect_all('systemmonitor')

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
    pathex=[base_dir, src_dir, python_lib, site_packages],
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
