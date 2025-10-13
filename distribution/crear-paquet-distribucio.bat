@echo off
REM Script per crear paquet de distribució - PythonTecnica_SOME
REM Autor: Sistema de distribució automàtica

echo.
echo ===============================================
echo    CREANT PAQUET DE DISTRIBUCIO
echo         PythonTecnica_SOME v1.0
echo ===============================================
echo.

REM Variables
set PACKAGE_NAME=PythonTecnica_SOME_Docker_v1.0
set PACKAGE_DIR=.\%PACKAGE_NAME%
set DIST_DIR=.\distribution

REM Crear directoris
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
mkdir "%DIST_DIR%"
mkdir "%PACKAGE_DIR%"

echo ✅ Directoris creats

REM Copiar fitxers essencials per Docker
echo.
echo 📁 Copiant fitxers essencials...

REM Fitxers Docker
copy "Dockerfile" "%PACKAGE_DIR%\" >nul
copy "docker-compose.yml" "%PACKAGE_DIR%\" >nul
copy ".dockerignore" "%PACKAGE_DIR%\" >nul
copy ".env.example" "%PACKAGE_DIR%\" >nul

REM Scripts d'instal·lació
copy "docker-install-windows.bat" "%PACKAGE_DIR%\" >nul
copy "docker-install-linux.sh" "%PACKAGE_DIR%\" >nul
copy "docker-manager.sh" "%PACKAGE_DIR%\" >nul
copy "docker-manager-windows.bat" "%PACKAGE_DIR%\" >nul

REM Documentació
copy "DOCKER_README.md" "%PACKAGE_DIR%\" >nul
copy "INSTRUCCIONS_INSTAL·LACIO.txt" "%PACKAGE_DIR%\" >nul

echo ✅ Fitxers Docker copiats

REM Copiar codi de l'aplicació
echo.
echo 📦 Copiant codi de l'aplicació...

REM Fitxer principal
copy "main_app.py" "%PACKAGE_DIR%\" >nul
copy "pytest.ini" "%PACKAGE_DIR%\" >nul

REM Carpetes essencials
xcopy "src" "%PACKAGE_DIR%\src" /e /i /q >nul
xcopy "config" "%PACKAGE_DIR%\config" /e /i /q >nul
xcopy "assets" "%PACKAGE_DIR%\assets" /e /i /q >nul 2>nul
xcopy "i18n" "%PACKAGE_DIR%\i18n" /e /i /q >nul 2>nul

REM Crear directoris buits necessaris
mkdir "%PACKAGE_DIR%\data" 2>nul
mkdir "%PACKAGE_DIR%\logs" 2>nul
mkdir "%PACKAGE_DIR%\sessions" 2>nul
mkdir "%PACKAGE_DIR%\compliance" 2>nul

echo ✅ Codi de l'aplicació copiat

REM Crear fitxer README per al paquet
echo.
echo 📝 Creant documentació del paquet...

echo # PAQUET DE DISTRIBUCIÓ - PythonTecnica_SOME > "%PACKAGE_DIR%\LLEGEIX-ME_PRIMER.txt"
echo. >> "%PACKAGE_DIR%\LLEGEIX-ME_PRIMER.txt"
echo Aquest és el paquet complet per instal·lar PythonTecnica_SOME amb Docker. >> "%PACKAGE_DIR%\LLEGEIX-ME_PRIMER.txt"
echo. >> "%PACKAGE_DIR%\LLEGEIX-ME_PRIMER.txt"
echo INSTRUCCIONS RÀPIDES: >> "%PACKAGE_DIR%\LLEGEIX-ME_PRIMER.txt"
echo. >> "%PACKAGE_DIR%\LLEGEIX-ME_PRIMER.txt"
echo Windows: >> "%PACKAGE_DIR%\LLEGEIX-ME_PRIMER.txt"
echo   1. Instal·la Docker Desktop >> "%PACKAGE_DIR%\LLEGEIX-ME_PRIMER.txt"
echo   2. Fes doble clic a: docker-install-windows.bat >> "%PACKAGE_DIR%\LLEGEIX-ME_PRIMER.txt"
echo. >> "%PACKAGE_DIR%\LLEGEIX-ME_PRIMER.txt"
echo Linux/macOS: >> "%PACKAGE_DIR%\LLEGEIX-ME_PRIMER.txt"
echo   1. Instal·la Docker >> "%PACKAGE_DIR%\LLEGEIX-ME_PRIMER.txt"
echo   2. Executa: ./docker-install-linux.sh >> "%PACKAGE_DIR%\LLEGEIX-ME_PRIMER.txt"
echo. >> "%PACKAGE_DIR%\LLEGEIX-ME_PRIMER.txt"
echo Per més detalls, consulta DOCKER_README.md >> "%PACKAGE_DIR%\LLEGEIX-ME_PRIMER.txt"

echo ✅ Documentació creada

REM Comprimir el paquet
echo.
echo 📦 Creant arxiu ZIP...

REM Utilitzar PowerShell per comprimir (funciona en Windows 10+)
powershell -Command "Compress-Archive -Path '%PACKAGE_DIR%\*' -DestinationPath '%DIST_DIR%\%PACKAGE_NAME%.zip' -Force" >nul 2>&1

if %errorlevel% equ 0 (
    echo ✅ Paquet ZIP creat correctament
) else (
    echo ⚠️  No es pot crear ZIP automàticament
    echo    Pots comprimir manualment la carpeta: %PACKAGE_DIR%
)

REM Neteja
rmdir /s /q "%PACKAGE_DIR%"

echo.
echo ================================================
echo ✅ PAQUET DE DISTRIBUCIÓ CREAT CORRECTAMENT!
echo ================================================
echo.
echo 📁 Localització: %DIST_DIR%\%PACKAGE_NAME%.zip
echo 📊 Contingut del paquet:
echo    - Aplicació completa amb Docker
echo    - Scripts d'instal·lació automàtica
echo    - Gestors de serveis
echo    - Documentació completa
echo.
echo 🚀 DISTRIBUCIÓ:
echo    Comparteix aquest ZIP amb altres usuaris
echo    Només necessitaran Docker instal·lat!
echo.
echo ================================================

pause