# -*- mode: python ; coding: utf-8 -*-


import glob

block_cipher = None

# En el distribuible se empaquetan los retos (robots.py los abre como
# codes/challengeN), los sketches de ejemplo del Braccio, el ejemplo mixto
# de 6 GDL y el sketch de medición real que usa la libreria Braccio
# (braccio_medicion_real). El único sketch de calibración del hardware físico
# que se deja FUERA del ejecutable es braccio_identify_m_ports.
_codes_datas = [(p, 'codes') for p in sorted(glob.glob('codes/challenge*'))]
_codes_datas += [
    ('codes/Prueba_Braccio_Library.ino', 'codes'),
    ('codes/Prueba_Servo_Library.ino', 'codes'),
    ('codes/braccio_medicion_real.ino', 'codes'),
    ('codes/braccio_medicion_real_servo.ino', 'codes'),
    ('codes/brazo_mixto_6gdl_rprprr.ino', 'codes'),
]


a = Analysis(
    ['simulator/main.py'],
    pathex=['simulator'],
    binaries=[],
    datas=[
        ('buttons', 'buttons'),
        ('assets', 'assets'),
        # Recursos del motor 3D del Braccio (mallas STL + preset DH). Viven en
        # simulator/assets y el motor3d los resuelve como <bundle>/assets/{stl,presets}.
        ('simulator/assets/stl', 'assets/stl'),
        ('simulator/assets/presets', 'assets/presets'),
        # Sólo los retos + los 3 sketches de ejemplo del Braccio (ver _codes_datas
        # arriba). Los PDFs de tutoriales los enlaza la interfaz desde tutorials/.
        *_codes_datas,
        ('tutorials', 'tutorials'),
        ('robot_data.json', '.'),
        ('manual-usuario.pdf', '.')
    ],
    hiddenimports=[],
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
    name='simulador',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon='assets/simlogo.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='simulador',
)
