@echo off
REM Script per crear el paquet d'instal·lació de PythonTecnica_SOME
REM Aquest script compila l'aplicació en un executable distributable

echo ========================================
echo BUILD PythonTecnica_SOME - Release Package
echo ========================================
echo.

echo [1/5] Verificant Python i PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller no esta instal·lat. Instal·lant...
    pip install pyinstaller
)

echo.
echo [2/5] Netejant builds anteriors...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo.
echo [3/5] Compilant aplicacio amb PyInstaller...
python -m PyInstaller --clean --noconfirm PythonTecnica_SOME.spec

if errorlevel 1 (
    echo.
    echo [ERROR] La compilacio ha fallat
    pause
    exit /b 1
)

echo.
echo [4/5] Creant estructura de distribucio...

REM Crear carpeta release
if not exist "release" mkdir release

REM Obtenir versio (pots canviar-la aquí)
set VERSION=2.0.0
set RELEASE_NAME=PythonTecnica_SOME_v%VERSION%

REM Crear carpeta de release amb versió
if exist "release\%RELEASE_NAME%" rmdir /s /q "release\%RELEASE_NAME%"
mkdir "release\%RELEASE_NAME%"

REM Copiar executable i dependencies
echo Copiant fitxers...
xcopy /E /I /Y "dist\PythonTecnica_SOME" "release\%RELEASE_NAME%\PythonTecnica_SOME"

REM Crear README per l'usuari
echo Creant documentacio...
(
echo PythonTecnica SOME - Versio %VERSION%
echo =====================================
echo.
echo INSTAL·LACIO:
echo 1. Descomprimeix aquest arxiu
echo 2. Executa PythonTecnica_SOME.exe
echo.
echo REQUISITS:
echo - Windows 10/11
echo - Connexio a la base de dades PostgreSQL ^(172.26.11.201^)
echo - Usuari: tecnica / Contrasenya: Some2025.!$%%
echo.
echo NOVETATS VERSIO %VERSION%:
echo - Modul d'estudis de capacitat implementat
echo - Auto-deteccio de schema 'qualitat'
echo - Millores en rendiment de queries
echo - Correccio de bugs
echo.
echo SUPORT:
echo Per problemes o dubtes, contacta amb l'administrador del sistema.
echo.
echo Data de build: %DATE% %TIME%
) > "release\%RELEASE_NAME%\README.txt"

REM Crear script d'instal·lació/actualització
(
echo @echo off
echo echo ========================================
echo echo PythonTecnica SOME - Actualitzacio
echo echo ========================================
echo echo.
echo echo Aquest script actualitzara l'aplicacio a la versio %VERSION%
echo echo.
echo pause
echo.
echo REM Detectar si hi ha una versio anterior
echo set OLD_INSTALL=%%LOCALAPPDATA%%\PythonTecnica_SOME
echo if exist "%%OLD_INSTALL%%" ^(
echo     echo [INFO] Versio anterior detectada
echo     echo [INFO] Creant backup de configuracio...
echo     if exist "%%OLD_INSTALL%%\config" ^(
echo         xcopy /E /I /Y "%%OLD_INSTALL%%\config" "config_backup"
echo     ^)
echo ^)
echo.
echo echo [INFO] Copiant nous fitxers...
echo xcopy /E /I /Y "PythonTecnica_SOME" "%%OLD_INSTALL%%"
echo.
echo REM Restaurar configuracio si existia
echo if exist "config_backup" ^(
echo     echo [INFO] Restaurant configuracio anterior...
echo     xcopy /E /I /Y "config_backup\database" "%%OLD_INSTALL%%\config\database"
echo     rmdir /s /q "config_backup"
echo ^)
echo.
echo echo.
echo echo ========================================
echo echo Actualitzacio completada!
echo echo ========================================
echo echo.
echo echo Pots executar l'aplicacio desde:
echo echo %%OLD_INSTALL%%\PythonTecnica_SOME.exe
echo echo.
echo pause
) > "release\%RELEASE_NAME%\INSTALAR.bat"

echo.
echo [5/5] Creant arxiu ZIP per distribucio...

REM Utilitzar PowerShell per crear ZIP
powershell -Command "Compress-Archive -Path 'release\%RELEASE_NAME%\*' -DestinationPath 'release\%RELEASE_NAME%.zip' -Force"

echo.
echo ========================================
echo BUILD COMPLETAT AMB EXIT!
echo ========================================
echo.
echo Paquet creat: release\%RELEASE_NAME%.zip
echo Tamany: 
dir "release\%RELEASE_NAME%.zip" | find ".zip"
echo.
echo Aquest arxiu esta llest per pujar a GitHub Release.
echo.
echo Per provar localment:
echo 1. Descomprimeix release\%RELEASE_NAME%.zip
echo 2. Executa INSTALAR.bat
echo.
pause
