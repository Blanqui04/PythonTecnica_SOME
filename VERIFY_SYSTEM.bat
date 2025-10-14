@echo off
echo ===============================================
echo    VERIFICACIO SISTEMA PYTHONTECNICA
echo ===============================================
echo.

echo Verificant Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no detectat
    echo Instal·leu Python des de https://www.python.org/
) else (
    echo [OK] Python detectat:
    python --version
)

echo.
echo Verificant pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip no detectat
) else (
    echo [OK] pip disponible
)

echo.
echo Verificant entorn virtual...
if exist "venv\Scripts\activate.bat" (
    echo [OK] Entorn virtual trobat
    call venv\Scripts\activate.bat
    echo [OK] Entorn virtual activat
    python -c "import sys; print(f'Python executable: {sys.executable}')"
) else (
    echo [WARNING] Entorn virtual no trobat
    echo Executeu SETUP.bat per crear-lo
)

echo.
echo Verificant dependències principals...
call venv\Scripts\activate.bat 2>nul
python -c "
try:
    import pandas, numpy, PyQt5, matplotlib
    print('[OK] Dependències principals instal·lades')
except ImportError as e:
    print(f'[ERROR] Dependència no trobada: {e}')
"

echo.
echo ===============================================
echo    VERIFICACIO COMPLETADA
echo ===============================================
pause