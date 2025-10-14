@echo off
echo ===============================================
echo    EXECUTANT PYTHONTECNICA SOME
echo ===============================================
echo.

REM Comprovar si l'entorn virtual existeix
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Entorn virtual no trobat!
    echo.
    echo Executeu primer:
    echo - SETUP.bat (instal·lació automàtica amb detecció d'errors)
    echo.
    echo O si teniu problemes amb C++ Build Tools:
    echo - instalacio\INSTALL_CPP_TOOLS.bat (guia Build Tools)
    echo.
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
    echo.
    echo Per diagnosticar problemes:
    echo - instalacio\VERIFY_SYSTEM.bat
    echo.
    pause
)

echo.
echo Aplicació tancada correctament
pause