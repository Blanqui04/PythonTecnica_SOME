# setup.py - Script per crear l'executable de l'aplicació
import sys
from cx_Freeze import setup, Executable
import os

# Dependències que s'han d'incloure
build_exe_options = {
    "packages": [
        "PyQt5", "pandas", "numpy", "psycopg2", "matplotlib", 
        "plotly", "openpyxl", "requests", "scipy", "statsmodels",
        "seaborn", "reportlab", "PyMuPDF"
    ],
    "include_files": [
        ("config/", "config/"),
        ("assets/", "assets/"),
        ("i18n/", "i18n/"),
        ("src/", "src/"),
    ],
    "excludes": ["tkinter", "unittest"],
    "zip_include_packages": ["encodings", "PySide2"],
}

# Configuració de l'executable
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Això evita que aparegui la consola

setup(
    name="PythonTecnica_SOME",
    version="1.0.0",
    description="Sistema de Gestió de Base de Dades Tècniques",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main_app.py",
            base=base,
            target_name="PythonTecnica_SOME.exe",
            icon="assets/images/gui/logo_some.png"  # Si tens un .ico
        )
    ]
)
