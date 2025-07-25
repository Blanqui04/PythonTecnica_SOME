@echo off
echo ========================================
echo   APLICACIO PYTHON TECNICA SOME
echo   Amb backups automatitzats cada 24h
echo ========================================
echo.

REM Activar entorn virtual si existeix
if exist "venv\Scripts\activate.bat" (
    echo Activant entorn virtual...
    call venv\Scripts\activate.bat
)

REM Executar aplicació principal
echo Iniciant aplicació...
python main_app.py

REM Pausa per veure possibles errors
if errorlevel 1 (
    echo.
    echo ERROR: L'aplicació ha fallat
    pause
)
