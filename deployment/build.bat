@echo off
echo ================================================
echo    BUILD I DEPLOYMENT - PythonTecnica_SOME
echo ================================================
echo.

REM Comprovar si Python està disponible
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no està instal·lat o no està en el PATH
    echo Si us plau, instal·la Python des de: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 1. Preparant entorn de build...
REM Instal·lar dependències de build
pip install -r ..\config\requirements.txt

echo.
echo 2. Construint aplicació...
REM Executar build
python build_and_deploy.py

echo.
echo 3. Build completat!
echo.
echo El paquet de deployment està disponible a: deployment_package\
echo.
echo Per instal·lar en ordinadors de l'empresa:
echo 1. Copia la carpeta 'deployment_package' a l'ordinador destí
echo 2. Executa 'install.bat' com a administrador
echo.
pause
