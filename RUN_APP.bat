@echo off
REM ========================================
REM PythonTecnica SOME - Executar Aplicació
REM ========================================

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

REM Executar aplicació sense finestra CMD (mode professional)
REM Utilitza pythonw.exe per amagar la consola
start "" "venv\Scripts\pythonw.exe" main_app.py

REM Nota: Si necessites veure errors de consola per debugging, executa run_app_debug.bat
