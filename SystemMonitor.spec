# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/systemmonitor/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src/systemmonitor/assets', 'assets'),
    ],
    hiddenimports=[
        'psutil',
        'pynvml',
        'GPUtil',
        'wmi',
        'win32com',
        'win32api',
        'win32gui',
        'win32process',
        'win32print',
        'win32service',
        'win32evtlog',
        'win32file',
        'win32net',
        'win32netcon',
        'win32pipe',
        'win32profile',
        'win32security',
        'win32service',
        'win32timezone',
        'win32wnet',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='src/systemmonitor/assets/icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)
