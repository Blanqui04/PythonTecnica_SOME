@echo off
echo ===============================================
echo    EXECUTANT PYTHONTECNICA SOME
echo ===============================================
echo.

REM Comprovar si l'entorn virtual existeix
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Entorn virtual no trobat!
    echo Executeu primer SETUP.bat per configurar l'aplicació
    pause
    exit /b 1
)

echo Activant entorn virtual...
call venv\Scripts\activate.bat

echo Executant aplicació...
python main_app.py

REM Mantenir la finestra oberta si hi ha errors
if errorlevel 1 (
    echo.
    echo [ERROR] L'aplicació ha finalitzat amb errors
    pause
)

echo.
echo Aplicació tancada correctament
pause