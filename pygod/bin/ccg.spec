# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

a = Analysis(
    ['ccg.py'],
    pathex=[],
    binaries=[],
    datas=[('../apps/py_scheduler/config/*', 'pygod/apps/py_scheduler/config'),\
           ('../apps/py_scheduler/ui/*', 'pygod/apps/py_scheduler/ui'),\
           ('../apps/py_scheduler/resources/icons/*', 'pygod/apps/py_scheduler/resources/icons'),\
           ('../apps/py_scheduler/resources/private/*', 'pygod/apps/py_scheduler/resources/private'),\
           ('../apps/py_scheduler/resources/stylesheets/*', 'pygod/apps/py_scheduler/resources/stylesheets'),\
           ('../apps/py_scheduler/widgets/*', 'pygod/apps/py_scheduler/widgets'),\
           ('../apps/ppt_worker/src/bible/*', 'pygod/apps/ppt_worker/src/bible'),\
           ('../apps/ppt_worker/src/bkg_slides/holy_dinner_option1/*', 'pygod/apps/ppt_worker/src/bkg_slides/holy_dinner_option1'),\
           ('../apps/ppt_worker/src/bkg_slides/holy_dinner_option2/*', 'pygod/apps/ppt_worker/src/bkg_slides/holy_dinner_option2'),\
           ('../apps/ppt_worker/src/bkg_slides/others/*', 'pygod/apps/ppt_worker/src/bkg_slides/others'),\
           ],
    hiddenimports=['numpy.random.common', 'numpy.random.bounded_integers', 'numpy.random.entropy','pptx'],
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
    [],
    exclude_binaries=True,
    name='ccg',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ccg.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ccg',
)
