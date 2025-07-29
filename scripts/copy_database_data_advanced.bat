@echo off
REM Script avançat per copiar dades entre bases de dades
REM Ofereix opcions per verificar abans de copiar

echo ===============================================
echo CÒPIA AVANÇADA DE DADES ENTRE BASES DE DADES
echo ===============================================
echo.
echo Opcions disponibles:
echo 1. Verificar connexions només
echo 2. Còpia amb confirmació
echo 3. Còpia sense confirmació
echo 4. Còpia + verificació integritat
echo 5. Sortir
echo.
echo ===============================================

REM Canviar al directori del projecte
cd /d "C:\Github\PythonTecnica_SOME\PythonTecnica_SOME"

REM Crear directori de logs si no existeix
if not exist "logs" mkdir logs

:menu
set /p opcio="Seleccioneu una opció (1-5): "

if "%opcio%"=="1" (
    echo.
    echo Verificant connexions...
    python scripts\copy_database_data_advanced.py --check-only
    goto end
)

if "%opcio%"=="2" (
    echo.
    echo Còpia amb confirmació...
    python scripts\copy_database_data_advanced.py
    goto end
)

if "%opcio%"=="3" (
    echo.
    echo Còpia sense confirmació...
    python scripts\copy_database_data_advanced.py --force
    goto end
)

if "%opcio%"=="4" (
    echo.
    echo Còpia amb verificació d'integritat...
    python scripts\copy_database_data_advanced.py --force --verify
    goto end
)

if "%opcio%"=="5" (
    echo Sortint...
    goto end
)

echo Opció no vàlida. Torneu a intentar-ho.
goto menu

:end
echo.
echo ===============================================
pause
