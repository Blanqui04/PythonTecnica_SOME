@echo off
title DEPLOYMENT PYTHONTECNICA_SOME
color 0A

echo.
echo ========================================================
echo        DEPLOYMENT EMPRESARIAL - PYTHONTECNICA_SOME
echo ========================================================
echo.
echo Aquest script prepara l'aplicacio per al deployment
echo a tots els PCs de l'empresa amb actualitzacions
echo automatiques i connexio automatica a la BBDD.
echo.
echo Servidor BBDD: 172.26.5.159:5433
echo Base de dades: documentacio_tecnica
echo.
pause

echo.
echo [1/4] Verificant Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instal.lat o no esta en el PATH
    echo.
    echo Si us plau, instal.la Python des de: https://www.python.org/downloads/
    echo Assegura't de marcar "Add Python to PATH" durant la instalacio
    echo.
    pause
    exit /b 1
)
echo Python detectat correctament!

echo.
echo [2/4] Creant estructura de deployment...
if not exist "deployment" mkdir deployment
if not exist "dist" mkdir dist
if not exist "build" mkdir build

echo.
echo [3/4] Instal.lant dependencies minimes (evita problemes antivirus)...
echo NOTA: Si tens problemes amb antivirus, usa deploy_portable.bat
echo.
pip install --user --no-cache-dir -r requirements_minimal.txt
if %errorlevel% neq 0 (
    echo.
    echo ATENCIO: Error instalant dependencies amb pip normal
    echo Provant instalacio alternativa...
    echo.
    REM Prova instalacio individual de packages critics
    pip install --user --no-cache-dir PyQt5
    pip install --user --no-cache-dir psycopg2-binary
    pip install --user --no-cache-dir pandas
    pip install --user --no-cache-dir numpy
    pip install --user --no-cache-dir matplotlib
    pip install --user --no-cache-dir requests
)

echo.
echo [4/4] El sistema esta preparat per al build!
echo.
echo OPCIONS DISPONIBLES:
echo.
echo 1. Build automatic (recomanat)
echo 2. Build manual amb PyInstaller  
echo 3. Configurar servidor d'actualitzacions
echo 4. Crear paquet de distribucio
echo 5. Sortir
echo.

:menu
set /p choice="Escull una opcio (1-5): "

if "%choice%"=="1" goto auto_build
if "%choice%"=="2" goto manual_build
if "%choice%"=="3" goto setup_server
if "%choice%"=="4" goto create_package
if "%choice%"=="5" goto end

echo Opcio no valida. Si us plau, escull 1-5.
goto menu

:auto_build
echo.
echo Executant build automatic...
python deployment\build_and_deploy.py
echo.
echo Build completat! Pots trobar els fitxers a la carpeta 'deployment_package'
goto end

:manual_build
echo.
echo Executant build manual amb PyInstaller...
pyinstaller --onedir --windowed --name "PythonTecnica_SOME" ^
    --add-data "config;config" ^
    --add-data "assets;assets" ^
    --add-data "i18n;i18n" ^
    --add-data "src;src" ^
    --hidden-import "PyQt5.QtCore" ^
    --hidden-import "PyQt5.QtGui" ^
    --hidden-import "PyQt5.QtWidgets" ^
    --hidden-import "psycopg2" ^
    main_app.py
echo.
echo Build manual completat! Executable a 'dist\PythonTecnica_SOME\'
goto end

:setup_server
echo.
echo Configurant servidor d'actualitzacions...
echo.
echo El servidor d'actualitzacions permet distribucio automatica
echo de noves versions a tots els PCs de l'empresa.
echo.
echo Per configurar:
echo 1. Escull un servidor de la xarxa (ex: 172.26.5.200)
echo 2. Executa: python deployment\server_setup.py
echo 3. Actualitza la URL a deployment\auto_updater.py
echo.
echo Vols obrir el fitxer auto_updater.py per editar? (s/n)
set /p edit="Resposta: "
if /i "%edit%"=="s" notepad deployment\auto_updater.py
goto end

:create_package
echo.
echo Creant paquet de distribucio...
echo.
echo Aquest proces crea un paquet llest per distribuir
echo a tots els PCs de l'empresa.
echo.

REM Crear estructura del paquet
if not exist "distribution_package" mkdir distribution_package
if not exist "distribution_package\app" mkdir distribution_package\app
if not exist "distribution_package\deployment" mkdir distribution_package\deployment

REM Copiar fitxers necessaris
echo Copiant aplicacio...
if exist "dist\PythonTecnica_SOME" (
    robocopy "dist\PythonTecnica_SOME" "distribution_package\app" /s /e
) else (
    echo AVISO: No s'ha trobat l'aplicacio compilada a dist\
    echo Executa primer el build (opcio 1 o 2)
)

echo Copiant scripts de deployment...
copy "deployment\*.py" "distribution_package\deployment\" >nul 2>&1
copy "requirements.txt" "distribution_package\" >nul 2>&1

REM Crear instal.lador
echo Creant instal.lador empresarial...
(
echo @echo off
echo title Instal.lacio PythonTecnica_SOME
echo echo.
echo echo Instal.lant PythonTecnica_SOME per a l'empresa...
echo echo.
echo echo Ubicacio d'installacio: C:\Program Files\SOME\PythonTecnica_SOME\
echo echo Connexio BBDD: 172.26.5.159:5433
echo echo.
echo.
echo REM Comprovar permisos d'administrador
echo net session ^>nul 2^>^&1
echo if %%errorlevel%% neq 0 ^(
echo     echo ERROR: Aquest script necessita permisos d'administrador
echo     echo Si us plau, executa com a administrador
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Instal.lar aplicacio
echo echo Instal.lant aplicacio...
echo python deployment\enterprise_installer.py app
echo.
echo echo.
echo echo Installacio completada!
echo echo Pots trobar l'aplicacio al menu d'inici o a l'escriptori.
echo echo.
echo pause
) > "distribution_package\install.bat"

REM Crear README
(
echo PAQUET DE DISTRIBUCIO - PYTHONTECNICA_SOME
echo ==========================================
echo.
echo Aquest paquet conté tot el necessari per instal.lar
echo PythonTecnica_SOME a qualsevol PC de l'empresa.
echo.
echo INSTRUCCIONS D'INSTALLACIO:
echo 1. Copia aquesta carpeta a l'ordinador desti
echo 2. Executa 'install.bat' com a administrador
echo 3. L'aplicacio s'instal.lara automaticament
echo.
echo CARACTERISTIQUES:
echo - Installacio automatica a C:\Program Files\SOME\
echo - Connexio automatica a la BBDD ^(172.26.5.159:5433^)
echo - Actualitzacions automatiques ^(si configurat^)
echo - Accessos directes al menu i escriptori
echo.
echo SUPORT: it@some.com
) > "distribution_package\README.txt"

echo.
echo Paquet de distribucio creat a: distribution_package\
echo.
echo Per distribuir:
echo 1. Copia la carpeta 'distribution_package' a cada PC
echo 2. Executa 'install.bat' com a administrador
echo.
goto end

:end
echo.
echo ========================================================
echo                     PROCES COMPLETAT
echo ========================================================
echo.
echo L'aplicacio esta preparada per al deployment empresarial!
echo.
echo PROXIMS PASSOS:
echo 1. Distribueix el paquet a tots els PCs
echo 2. Executa la installacio en cada PC
echo 3. Configura el servidor d'actualitzacions ^(opcional^)
echo.
echo Per a mes informacio, consulta INSTRUCCIONS_DEPLOYMENT.md
echo.
pause
