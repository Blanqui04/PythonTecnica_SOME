@echo off
REM =====================================================
REM Script d'automatització Scanner Projectes
REM Sincronització del path \\gompc\kiosk
REM =====================================================

echo.
echo =====================================================
echo        AUTOMATITZACIO SCANNER PROJECTES
echo =====================================================
echo.
echo Path: \\gompc\kiosk
echo Maquina: Scanner Projectes
echo Data: %date% %time%
echo.

REM Canviar al directori del projecte
cd /d "%~dp0\.."

REM Activar entorn virtual si existeix
if exist "venv\Scripts\activate.bat" (
    echo Activant entorn virtual...
    call venv\Scripts\activate.bat
)

REM Executar script de sincronització
echo Executant sincronitzacio Scanner Projectes...
python automatitzacions\project_scanner_auto.py

REM Capturar codi de sortida
set EXIT_CODE=%ERRORLEVEL%

echo.
echo =====================================================
if %EXIT_CODE%==0 (
    echo           SINCRONITZACIO COMPLETADA
    echo                   ÈXIT!
) else (
    echo           SINCRONITZACIO FALLIDA
    echo                  ERROR!
    echo Codi de sortida: %EXIT_CODE%
)
echo =====================================================
echo.

REM Pausa per veure resultats (comentar per automatització completa)
pause

exit /b %EXIT_CODE%
