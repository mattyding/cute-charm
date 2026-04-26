# -*- mode: python ; coding: utf-8 -*-
# Run with: pyinstaller build.spec

APP_NAME = "Gen 4 Cute Charm Glitch Tool"

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=["PyQt6.sip"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Gen4CuteCharmTool",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="Gen4CuteCharmTool",
)

# Mac .app bundle — ignored on Windows/Linux
app = BUNDLE(
    coll,
    name=f"{APP_NAME}.app",
    icon=None,
    bundle_identifier="com.cutecharm.gen4tool",
    info_plist={
        "CFBundleShortVersionString": "1.0.0",
        "NSHighResolutionCapable": True,       # crisp on Retina displays
        "LSMinimumSystemVersion": "10.13.0",
    },
)
