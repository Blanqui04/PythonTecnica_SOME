@echo off
REM Script per executar la neteja automàtica universal de fitxers temporals
REM Funciona amb tots els clients: ZF, SEAT, BMW, Audi, Mercedes, etc.

cd /d "%~dp0.."

echo ==========================================
echo    Neteja automatica UNIVERSAL
echo    Tots els clients i projectes
echo ==========================================
echo.

REM Crear directori de logs si no existeix
if not exist "logs" mkdir logs

REM Opcions d'execució
echo Selecciona el tipus de neteja:
echo.
echo 1. Neteja general de tots els fitxers antics
echo 2. Neteja per client específic (ZF, SEAT, BMW, etc.)
echo 3. Neteja agressiva general
echo 4. Test de funcionalitat
echo.

set /p choice="Introdueix la teva opció (1-4): "

if "%choice%"=="1" goto neteja_general
if "%choice%"=="2" goto neteja_client
if "%choice%"=="3" goto neteja_agressiva
if "%choice%"=="4" goto test_funcionalitat
goto invalid_choice

:neteja_general
echo.
echo [%date% %time%] Executant neteja general...
python maintenance\auto_cleanup.py
goto end

:neteja_client
echo.
set /p client="Introdueix el nom del client (ZF, SEAT, BMW, etc.): "
set /p project="Introdueix la referència del projecte: "
echo.
echo [%date% %time%] Executant neteja per %client% / %project%...
python maintenance\auto_cleanup.py --client "%client%" --project-id "%project%" --universal
goto end

:neteja_agressiva
echo.
echo [%date% %time%] Executant neteja agressiva...
python maintenance\auto_cleanup.py --aggressive
goto end

:test_funcionalitat
echo.
echo [%date% %time%] Executant tests de funcionalitat...
python tests\test_universal_cleanup.py
goto end

:invalid_choice
echo.
echo Opció no vàlida. Executant neteja general per defecte...
python maintenance\auto_cleanup.py

:end
echo.
echo Operació completada. Revisa el fitxer logs\auto_cleanup.log per més detalls.
echo.

REM Mostrar estadístiques ràpides
echo ==========================================
echo           ESTADISTIQUES
echo ==========================================
if exist "logs\auto_cleanup.log" (
    echo Últimes entrades del log:
    echo.
    tail -n 5 logs\auto_cleanup.log 2>nul || (
        echo [Log disponible per revisió manual]
    )
)
echo.

REM Opcional: Pausa per veure els resultats
pause
