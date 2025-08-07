# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.building.build_main import Analysis, PYZ, EXE, BUNDLE

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Skeincare',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    a.binaries,
    a.datas,
    name='Skeincare.app',
    icon='thread.png',
    bundle_identifier=None,
    info_plist={
        'NSHighResolutionCapable': 'True',
        'NSPrincipalClass': 'NSApplication',
        'CFBundleShortVersionString': '1.0.0',
    },
)