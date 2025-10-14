@echo off
echo ===============================================
echo    PREPARACIO FORK ESTABLE - PythonTecnica
echo ===============================================
echo.

echo Aquest script prepara el repositori per crear un fork estable
echo.

echo 1. Netejant fitxers de desenvolupament...
if exist "__pycache__" rmdir /s /q __pycache__ 2>nul
if exist "*.pyc" del /s /q *.pyc 2>nul
if exist "build" rmdir /s /q build 2>nul
if exist "temp_build" rmdir /s /q temp_build 2>nul
if exist "venv" rmdir /s /q venv 2>nul
if exist "venv_build" rmdir /s /q venv_build 2>nul
echo [OK] Fitxers temporals eliminats

echo.
echo 2. Verificant fitxers essencials...
if exist "main_app.py" (
    echo [OK] main_app.py present
) else (
    echo [ERROR] main_app.py no trobat!
    pause
    exit /b 1
)

if exist "requirements.txt" (
    echo [OK] requirements.txt present
) else (
    echo [ERROR] requirements.txt no trobat!
    pause
    exit /b 1
)

if exist "SETUP.bat" (
    echo [OK] SETUP.bat present
) else (
    echo [ERROR] SETUP.bat no trobat!
    pause
    exit /b 1
)

if exist "RUN_APP.bat" (
    echo [OK] RUN_APP.bat present
) else (
    echo [ERROR] RUN_APP.bat no trobat!
    pause
    exit /b 1
)

echo.
echo 3. Creant documentació de versió estable...
echo # PythonTecnica SOME - Fork Estable > STABLE_RELEASE.md
echo. >> STABLE_RELEASE.md
echo Data de preparacio: %date% %time% >> STABLE_RELEASE.md
echo Versio: 1.0-stable >> STABLE_RELEASE.md
echo. >> STABLE_RELEASE.md
echo Aquest fork conte la versio estable per distribucio. >> STABLE_RELEASE.md
echo [OK] Documentació de versió creada

echo.
echo 4. Verificant dependències...
python -c "
import sys
print('Python version:', sys.version)
try:
    with open('requirements.txt', 'r') as f:
        deps = len([l for l in f.readlines() if l.strip() and not l.startswith('#')])
    print(f'Dependencies defined: {deps}')
    print('[OK] Requirements file valid')
except Exception as e:
    print(f'[ERROR] {e}')
"

echo.
echo ===============================================
echo    PREPARACIO COMPLETADA
echo ===============================================
echo.
echo El repositori esta preparat per crear el fork estable.
echo.
echo Passos seguents:
echo 1. Crear fork a GitHub amb nom: PythonTecnica-SOME-Stable
echo 2. Pujar aquests canvis al fork
echo 3. Crear release estable
echo.
pause