@echo off
REM ============================================================
REM Script de sincronització automàtica de bases de dades
REM Executa cada nit a les 24:00h
REM ============================================================

echo.
echo ============================================================
echo    SINCRONITZACIO AUTOMATICA DE BASES DE DADES
echo    Data: %date% %time%
echo ============================================================
echo.

REM Canviar al directori del projecte
cd /d C:\Github\PythonTecnica_SOME\PythonTecnica_SOME

REM Activar entorn virtual si existeix
if exist venv\Scripts\activate.bat (
    echo Activant entorn virtual...
    call venv\Scripts\activate.bat
)

REM Executar sincronització incremental (per defecte)
echo.
echo Executant sincronitzacio incremental...
python scripts\sync_databases.py

REM Verificar resultat
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo    SINCRONITZACIO COMPLETADA AMB EXIT!
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo    ERROR EN LA SINCRONITZACIO! Codi: %ERRORLEVEL%
    echo ============================================================
)

echo.
pause
