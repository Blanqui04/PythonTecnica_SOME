@echo off
REM ========================================
REM PythonTecnica SOME - Executar (DEBUG MODE)
REM ========================================
REM Aquesta versió mostra la consola per veure errors i missatges

REM Verificar que l'entorn virtual existeix
if not exist "venv\Scripts\activate.bat" (
    echo.
    echo [ERROR] L'entorn virtual no existeix!
    echo.
    echo Si us plau, executa primer: setup.bat
    echo.
    pause
    exit /b 1
)

echo ========================================
echo  MODE DEBUG - Consola visible
echo ========================================
echo.
echo Iniciant aplicacio amb logs visibles...
echo Si veus errors, revisa els logs a: data\logs\
echo.

REM Activar entorn virtual i executar aplicació amb consola
call venv\Scripts\activate.bat
python main_app.py

REM Si hi ha error, mostrar missatge
if errorlevel 1 (
    echo.
    echo ========================================
    echo [ERROR] L'aplicacio ha fallat
    echo ========================================
    echo.
    echo Comprova els logs a: data\logs\
    echo.
    pause
    exit /b 1
)

echo.
echo Aplicacio tancada correctament
pause
