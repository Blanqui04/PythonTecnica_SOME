@echo off
REM ========================================
REM PythonTecnica SOME - Setup/Instal·lació
REM ========================================
REM
REM Aquest script prepara l'entorn per executar l'aplicació
REM Només cal executar-lo UNA VEGADA després de descarregar

echo.
echo ========================================
echo PythonTecnica SOME - Setup
echo ========================================
echo.
echo Aquest script instal·lara tot el necessari per executar l'aplicacio.
echo Nomes cal executar-lo una vegada.
echo.
pause

REM Verificar que Python esta instal·lat
echo.
echo [1/4] Verificant Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python no esta instal·lat!
    echo.
    echo Si us plau, instal·la Python 3.9 o superior des de:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Durant la instalacio, marca la opcio:
    echo [X] Add Python to PATH
    echo.
    pause
    exit /b 1
)

python --version
echo [OK] Python detectat correctament

REM Crear entorn virtual
echo.
echo [2/4] Creant entorn virtual...
if exist "venv" (
    echo [INFO] Entorn virtual ja existeix, saltant...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] No s'ha pogut crear l'entorn virtual
        pause
        exit /b 1
    )
    echo [OK] Entorn virtual creat
)

REM Activar entorn virtual
echo.
echo [3/4] Activant entorn virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] No s'ha pogut activar l'entorn virtual
    pause
    exit /b 1
)
echo [OK] Entorn virtual activat

REM Instal·lar dependencies
echo.
echo [4/4] Instal·lant dependencies...
echo [INFO] Aixo pot trigar uns minuts...
echo.
python -m pip install --upgrade pip
pip install -r config/requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Hi ha hagut problemes instal·lant algunes dependencies
    echo.
    echo Intenta executar manualment:
    echo   venv\Scripts\activate
    echo   pip install -r config/requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo SETUP COMPLETAT AMB EXIT!
echo ========================================
echo.
echo Ara pots executar l'aplicacio amb:
echo   run_app.bat
echo.
echo O manualment:
echo   venv\Scripts\activate
echo   python main_app.py
echo.
pause
