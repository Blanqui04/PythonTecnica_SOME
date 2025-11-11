@echo off
REM ========================================
REM PythonTecnica SOME - Prerequisites Check
REM ========================================
echo.
echo ========================================
echo  VERIFICACIO DE PREREQUISITS
echo ========================================
echo.

REM Check Python installation
echo [1/4] Verificant Python...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no esta instal·lat o no esta al PATH!
    echo.
    echo SOLUCIO:
    echo   1. Descarrega Python desde: https://www.python.org/downloads/
    echo   2. Instal·la marcant "Add Python to PATH"
    echo   3. Reinicia l'ordinador
    echo   4. Torna a executar aquest script
    echo.
    pause
    exit /b 1
)

python --version
echo [OK] Python detectat correctament
echo.

REM Check Python version
echo [2/4] Verificant versio de Python...
for /f "tokens=2 delims= " %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% LSS 3 (
    echo [ERROR] Python versio massa antiga: %PYTHON_VERSION%
    echo Es necessita Python 3.9 o superior
    echo.
    pause
    exit /b 1
)

if %MAJOR% EQU 3 if %MINOR% LSS 9 (
    echo [ERROR] Python versio massa antiga: %PYTHON_VERSION%
    echo Es necessita Python 3.9 o superior
    echo.
    pause
    exit /b 1
)

echo [OK] Python %PYTHON_VERSION% - Compatible
echo.

REM Check pip
echo [3/4] Verificant pip...
python -m pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] pip no esta instal·lat!
    echo.
    echo SOLUCIO:
    echo   python -m ensurepip --upgrade
    echo.
    pause
    exit /b 1
)

python -m pip --version
echo [OK] pip disponible
echo.

REM Check network connectivity (optional)
echo [4/4] Verificant connexio a base de dades...
ping -n 1 172.26.11.201 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [AVIS] No es pot accedir al servidor de BD: 172.26.11.201
    echo Assegura't que estas connectat a la xarxa interna.
    echo.
    echo L'aplicacio podra obrir-se igualment, pero sense accés a dades.
    echo.
) else (
    echo [OK] Servidor de BD accessible
    echo.
)

REM Summary
echo ========================================
echo  RESUM
echo ========================================
echo.
echo [OK] Python instalat i configurat
echo [OK] pip disponible
echo.
echo Ara pots executar:
echo   1. setup.bat      (primera vegada)
echo   2. run_app.bat    (executar aplicacio)
echo.
echo ========================================
pause
