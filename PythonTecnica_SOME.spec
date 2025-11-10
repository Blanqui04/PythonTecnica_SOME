# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from pathlib import Path

# Definir variables
app_name = 'PythonTecnica_SOME'
main_script = 'main_app.py'

# Recopilar tots els submòduls necessaris
hiddenimports = [
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'pandas',
    'numpy',
    'scipy',
    'scipy.stats',
    'scipy.special',
    'openpyxl',
    'psycopg2',
    'matplotlib',
    'matplotlib.backends.backend_qt5agg',
    'plotly',
    'statsmodels',
    'statsmodels.api',
    'statsmodels.formula.api',
    'reportlab',
    'seaborn',
    'sklearn',
    'requests',
    'schedule',
    'PyMuPDF',
    'fitz',
    'PyPDF2',
    # Submòduls de l'aplicació
    'src.gui',
    'src.services',
    'src.database',
    'src.data_processing',
    'src.models',
    'src.reports',
    'src.utils',
    'src.auth',
    'src.compliance',
    'src.dashboard',
    'src.exceptions',
    'src.logs',
]

# Dades a incloure
datas = [
    ('config', 'config'),
    ('assets', 'assets'),
    ('i18n', 'i18n'),
    ('src', 'src'),
]

# Binaris externs
binaries = []

a = Analysis(
    [main_script],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'test',
        'unittest',
        'email',
        'http',
        'urllib',
        'xml',
        'pydoc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # False per a GUI, True per veure debug
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/images/gui/icon.ico' if Path('assets/images/gui/icon.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)
