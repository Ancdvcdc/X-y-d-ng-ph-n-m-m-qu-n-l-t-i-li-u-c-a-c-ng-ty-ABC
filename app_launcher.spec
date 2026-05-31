# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app_launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('client/login.ui', 'client'),
        ('client/mainwindow.ui', 'client'),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DocumentManagerApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    onefile=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='DocumentManagerApp',
)
