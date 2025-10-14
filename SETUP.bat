@echo off
echo ===============================================
echo    CONFIGURACIO PYTHONTECNICA SOME
echo ===============================================
echo.

REM Comprovar si Python està instal·lat
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no està instal·lat o no està al PATH
    echo Descarrega Python des de: https://www.python.org/downloads/
    echo Assegureu-vos de marcar "Add Python to PATH" durant la instal·lació
    pause
    exit /b 1
)

echo [OK] Python detectat:
python --version

echo.
echo Creant entorn virtual...
python -m venv venv

echo.
echo Activant entorn virtual...
call venv\Scripts\activate.bat

echo.
echo Actualitzant pip...
python -m pip install --upgrade pip

echo.
echo Instal·lant dependències...
pip install -r requirements.txt

echo.
echo ===============================================
echo    CONFIGURACIO COMPLETADA!
echo ===============================================
echo.
echo Per executar l'aplicació, utilitzeu: RUN_APP.bat
echo.
pause