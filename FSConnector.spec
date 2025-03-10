# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['FSConnector.py'],
    pathex=['C:\\Users\\wu_cc\\AppData\\Local\\Programs\\Python\\Python310\\Lib\\site-packages', 'http', 'webview', 'websockets', 'asyncio', 'asyncua', 'conn_opcua', 'conn_ur_vrc', 'conn_web'],
    binaries=[],
    datas=[('aitester.html', '.'), ('aitester.js', '.'), ('Fastsuite_E2_Icon.ico', '.'), ('CENIT_gross_RGB.png', '.'), ('webview', 'webview')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FSConnector',
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
    icon=['Fastsuite_E2_Icon.ico'],
)
