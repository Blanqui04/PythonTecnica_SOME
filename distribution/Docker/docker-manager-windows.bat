@echo off
REM Gestor Docker per Windows - PythonTecnica_SOME

setlocal enabledelayedexpansion

:menu
cls
echo.
echo ========================================
echo      GESTOR DOCKER PYTHONTECNICA
echo ========================================
echo.
echo 1. Iniciar aplicacio
echo 2. Parar aplicacio
echo 3. Reiniciar aplicacio
echo 4. Veure logs
echo 5. Estat dels serveis
echo 6. Fer backup
echo 7. Obrir shell app
echo 8. Obrir shell base de dades
echo 9. Actualitzar aplicacio
echo 0. Sortir
echo.
set /p choice="Selecciona una opcio (0-9): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto status
if "%choice%"=="6" goto backup
if "%choice%"=="7" goto shell
if "%choice%"=="8" goto dbshell
if "%choice%"=="9" goto update
if "%choice%"=="0" goto exit
goto menu

:start
echo.
echo Iniciant serveis...
docker-compose up -d
if %errorlevel% equ 0 (
    echo ✅ Serveis iniciats correctament!
) else (
    echo ❌ Error iniciant serveis!
)
pause
goto menu

:stop
echo.
echo Parant serveis...
docker-compose down
if %errorlevel% equ 0 (
    echo ✅ Serveis aturats correctament!
) else (
    echo ❌ Error aturant serveis!
)
pause
goto menu

:restart
echo.
echo Reiniciant serveis...
docker-compose restart
if %errorlevel% equ 0 (
    echo ✅ Serveis reiniciats correctament!
) else (
    echo ❌ Error reiniciant serveis!
)
pause
goto menu

:logs
echo.
echo Mostrant logs de l'aplicacio...
echo Prem Ctrl+C per sortir dels logs
echo.
docker-compose logs -f pythontecnica_app
goto menu

:status
echo.
echo Estat dels contenidors:
docker-compose ps
echo.
pause
goto menu

:backup
echo.
echo Creant backup de la base de dades...
if not exist "data\backup" mkdir "data\backup"
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set datetime=%mydate%_%mytime%
docker-compose exec postgres pg_dump -U pythontecnica_user pythontecnica_db > "data\backup\backup_%datetime%.sql"
if %errorlevel% equ 0 (
    echo ✅ Backup creat: data\backup\backup_%datetime%.sql
) else (
    echo ❌ Error creant backup!
)
pause
goto menu

:shell
echo.
echo Obrint shell del contenidor app...
docker-compose exec pythontecnica_app bash
goto menu

:dbshell
echo.
echo Obrint shell de PostgreSQL...
docker-compose exec postgres psql -U pythontecnica_user -d pythontecnica_db
goto menu

:update
echo.
echo Actualitzant aplicacio...
echo Parant serveis...
docker-compose down
echo Reconstruint imatges...
docker-compose build --no-cache
echo Iniciant serveis actualitzats...
docker-compose up -d
if %errorlevel% equ 0 (
    echo ✅ Aplicacio actualitzada correctament!
) else (
    echo ❌ Error actualitzant aplicacio!
)
pause
goto menu

:exit
echo.
echo Sortint del gestor...
exit /b 0