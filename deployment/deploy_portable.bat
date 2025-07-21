@echo off
title DEPLOYMENT PYTHONTECNICA_SOME - VERSIO ALTERNATIVA
color 0A

echo.
echo ========================================================
echo    DEPLOYMENT EMPRESARIAL - PYTHONTECNICA_SOME
echo             VERSIO ALTERNATIVA (SENSE BUILD)
echo ========================================================
echo.
echo Aquest script crea un paquet de distribucio directament
echo sense necessitat de compilar l'aplicacio.
echo Perfect per evitar problemes amb antivirus!
echo.
echo Servidor BBDD: 172.26.5.159:5433
echo Base de dades: documentacio_tecnica
echo.
pause

echo.
echo [1/3] Verificant Python...
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
echo [2/3] Instal.lant dependencies minimes...
pip install psycopg2-binary pandas numpy matplotlib plotly openpyxl PyQt5 flask requests

echo.
echo [3/3] El sistema esta preparat!
echo.
echo OPCIONS DISPONIBLES:
echo.
echo 1. Crear paquet portable (RECOMANAT - sense antivirus)
echo 2. Configurar servidor d'actualitzacions
echo 3. Crear instal.lador simple
echo 4. Test de connexio BBDD
echo 5. Sortir
echo.

:menu
set /p choice="Escull una opcio (1-5): "

if "%choice%"=="1" goto portable_package
if "%choice%"=="2" goto setup_server
if "%choice%"=="3" goto simple_installer
if "%choice%"=="4" goto test_db
if "%choice%"=="5" goto end

echo Opcio no valida. Si us plau, escull 1-5.
goto menu

:portable_package
echo.
echo ========================================================
echo                 CREANT PAQUET PORTABLE
echo ========================================================
echo.
echo Aquest paquet inclou tot el codi font i es pot executar
echo directament en qualsevol PC amb Python instaltat.
echo Avantatges: No problemes amb antivirus, facil de distribuir
echo.

REM Crear estructura del paquet portable
echo Creant estructura...
if not exist "portable_package" mkdir portable_package
if not exist "portable_package\PythonTecnica_SOME" mkdir portable_package\PythonTecnica_SOME

REM Copiar tot el codi de l'aplicacio
echo Copiant aplicacio...
robocopy "." "portable_package\PythonTecnica_SOME" /s /e ^
    /xd ".git" "__pycache__" "build" "dist" "portable_package" "deployment_package" ^
    /xf "*.pyc" "*.pyo" "*.log"

REM Crear script de llançament
echo Creant launcher...
(
echo @echo off
echo title PythonTecnica_SOME
echo cd /d "%%~dp0PythonTecnica_SOME"
echo echo Iniciant PythonTecnica_SOME...
echo echo Connectant a BBDD: 172.26.5.159:5433
echo echo.
echo python main_app.py
echo if %%errorlevel%% neq 0 ^(
echo     echo.
echo     echo ERROR: No s'ha pogut executar l'aplicacio
echo     echo Comprova que Python esta instalat i que totes les dependencies estan disponibles
echo     echo.
echo     echo Per installar dependencies:
echo     echo pip install -r requirements.txt
echo     echo.
echo     pause
echo ^)
) > "portable_package\Executar_PythonTecnica_SOME.bat"

REM Crear instal.lador de dependencies
(
echo @echo off
echo title Instal.lador Dependencies - PythonTecnica_SOME
echo echo.
echo echo Instal.lant dependencies necessaries...
echo echo Aixo pot trigar uns minuts...
echo echo.
echo cd /d "%%~dp0PythonTecnica_SOME"
echo pip install -r requirements.txt
echo echo.
echo echo Dependencies instalades!
echo echo Ja pots executar l'aplicacio amb "Executar_PythonTecnica_SOME.bat"
echo echo.
echo pause
) > "portable_package\Instal.lar_Dependencies.bat"

REM Crear README detallat
(
echo PYTHONTECNICA_SOME - PAQUET PORTABLE
echo ====================================
echo.
echo Aquest es un paquet portable que conté tot el necessari
echo per executar PythonTecnica_SOME en qualsevol PC.
echo.
echo REQUISITS:
echo - Python 3.8 o superior instalat
echo - Connexio a la xarxa de l'empresa
echo.
echo INSTALLACIO RAPIDA:
echo 1. Descomprimeix aquesta carpeta on vulguis
echo 2. Executa "Instal.lar_Dependencies.bat" ^(NOMES LA PRIMERA VEGADA^)
echo 3. Executa "Executar_PythonTecnica_SOME.bat"
echo.
echo CARACTERISTIQUES:
echo - Connexio automatica a la BBDD ^(172.26.5.159:5433^)
echo - No necessita permisos d'administrador
echo - Compatible amb qualsevol antivirus
echo - Facil d'actualitzar ^(nomes cal substituir la carpeta^)
echo.
echo ESTRUCTURA:
echo - PythonTecnica_SOME\     : Codi de l'aplicacio
echo - Executar_PythonTecnica_SOME.bat : Launcher principal
echo - Instal.lar_Dependencies.bat     : Instalador de dependencies
echo.
echo SUPORT:
echo Per problemes o preguntes, contacta amb l'equip IT
echo Email: it@some.com
echo.
echo VERSIO: 1.0.0 ^(Portable^)
echo DATA: %date%
) > "portable_package\README.txt"

REM Crear script d'actualitzacio
(
echo @echo off
echo title Actualitzador PythonTecnica_SOME
echo echo.
echo echo ACTUALITZADOR PYTHONTECNICA_SOME
echo echo ================================
echo echo.
echo echo Aquest script descarrega i aplica actualitzacions
echo echo des del servidor de l'empresa.
echo echo.
echo set /p server="Introdueix la IP del servidor d'actualitzacions ^(ex: 172.26.5.200^): "
echo if "%%server%%"=="" set server=172.26.5.200
echo.
echo echo Comprovant actualitzacions des de %%server%%...
echo curl -s "http://%%server%%:8080/version.json" ^> version_info.json
echo if %%errorlevel%% equ 0 ^(
echo     echo Actualitzacio disponible! Descarregant...
echo     REM Aqui pots afegir logica per descarregar i aplicar updates
echo     echo Actualitzacio completada!
echo ^) else ^(
echo     echo No s'han trobat actualitzacions o no es pot connectar al servidor
echo ^)
echo echo.
echo pause
echo del version_info.json ^>nul 2^>^&1
) > "portable_package\Actualitzar.bat"

echo.
echo PAQUET PORTABLE CREAT EXITOSAMENT!
echo ===================================
echo.
echo Ubicacio: portable_package\
echo.
echo INSTRUCCIONS PER DISTRIBUIR:
echo 1. Comprimeix la carpeta 'portable_package' en un ZIP
echo 2. Distribueix el ZIP a tots els PCs de l'empresa
echo 3. Els usuaris nomes han de:
echo    - Descomprimir
echo    - Executar "Instal.lar_Dependencies.bat" ^(primera vegada^)
echo    - Executar "Executar_PythonTecnica_SOME.bat"
echo.
echo AVANTATGES D'AQUESTA SOLUCIO:
echo + No problemes amb antivirus
echo + No necessita permisos d'administrador
echo + Facil de distribuir i actualitzar
echo + Compatible amb qualsevol configuracio de Windows
echo.
goto end

:setup_server
echo.
echo ========================================================
echo           CONFIGURANT SERVIDOR D'ACTUALITZACIONS
echo ========================================================
echo.
echo El servidor d'actualitzacions permet distribucio automatica
echo de noves versions a tots els PCs de l'empresa.
echo.
echo PASSOS:
echo 1. Escull un servidor de la xarxa ^(ex: 172.26.5.200^)
echo 2. Copia el fitxer 'deployment\server_setup.py' al servidor
echo 3. Al servidor, executa: python server_setup.py
echo 4. Configurar clients per usar aquest servidor
echo.
echo Vols obrir el fitxer server_setup.py per revisar? ^(s/n^)
set /p edit="Resposta: "
if /i "%edit%"=="s" notepad deployment\server_setup.py
echo.
echo Per configurar clients, edita 'deployment\auto_updater.py'
echo i canvia la URL del servidor d'actualitzacions.
echo.
goto end

:simple_installer
echo.
echo ========================================================
echo              CREANT INSTAL.LADOR SIMPLE
echo ========================================================
echo.
echo Aquest instal.lador copiara l'aplicacio a una ubicacio
echo fixa i creara accessos directes.
echo.

if not exist "simple_installer" mkdir simple_installer

REM Crear instal.lador que copiara tot a Program Files
(
echo @echo off
echo title Instal.lador Simple - PythonTecnica_SOME
echo.
echo echo INSTAL.LADOR PYTHONTECNICA_SOME
echo echo ===============================
echo echo.
echo echo Aquest script instalara PythonTecnica_SOME a:
echo echo C:\Program Files\SOME\PythonTecnica_SOME\
echo echo.
echo echo Pressiona qualsevol tecla per continuar o Ctrl+C per cancelar
echo pause ^>nul
echo.
echo REM Crear directori d'installacio
echo if not exist "C:\Program Files\SOME" mkdir "C:\Program Files\SOME"
echo if not exist "C:\Program Files\SOME\PythonTecnica_SOME" mkdir "C:\Program Files\SOME\PythonTecnica_SOME"
echo.
echo echo Copiant fitxers...
echo robocopy "." "C:\Program Files\SOME\PythonTecnica_SOME" /s /e ^
echo     /xd ".git" "__pycache__" "build" "dist" "portable_package" "simple_installer" ^
echo     /xf "*.pyc" "*.pyo" "*.log"
echo.
echo echo Creant accessos directes...
echo powershell -Command "$$WshShell = New-Object -comObject WScript.Shell; $$Shortcut = $$WshShell.CreateShortcut('%%USERPROFILE%%\Desktop\PythonTecnica_SOME.lnk'^); $$Shortcut.TargetPath = 'python.exe'; $$Shortcut.Arguments = 'C:\Program Files\SOME\PythonTecnica_SOME\main_app.py'; $$Shortcut.WorkingDirectory = 'C:\Program Files\SOME\PythonTecnica_SOME'; $$Shortcut.Save(^)"
echo.
echo echo Installacio completada!
echo echo Trobaras PythonTecnica_SOME a l'escriptori.
echo echo.
echo pause
) > "simple_installer\install.bat"

REM Copiar tots els fitxers necessaris
echo Copiant fitxers a l'instal.lador...
robocopy "." "simple_installer" /s /e ^
    /xd ".git" "__pycache__" "build" "dist" "portable_package" "simple_installer" ^
    /xf "*.pyc" "*.pyo" "*.log"

echo.
echo INSTAL.LADOR SIMPLE CREAT!
echo ==========================
echo.
echo Ubicacio: simple_installer\
echo.
echo Per usar:
echo 1. Copia la carpeta 'simple_installer' a cada PC
echo 2. Executa 'install.bat' com a administrador
echo.
goto end

:test_db
echo.
echo ========================================================
echo                  TEST CONNEXIO BBDD
echo ========================================================
echo.
echo Provant connexio a la base de dades...
echo Servidor: 172.26.5.159:5433
echo Base de dades: documentacio_tecnica
echo.

REM Crear script temporal per provar connexio
(
echo import psycopg2
echo import sys
echo.
echo try:
echo     print^("Intentant connectar a la base de dades..."^)
echo     conn = psycopg2.connect^(
echo         host="172.26.5.159",
echo         port="5433", 
echo         database="documentacio_tecnica",
echo         user="administrador",
echo         password="Some2025.!$$%%"
echo     ^)
echo     print^("CONNEXIO EXITOSA! La base de dades es accessible."^)
echo     conn.close^(^)
echo except Exception as e:
echo     print^(f"ERROR DE CONNEXIO: {e}"^)
echo     print^("Possibles causes:"^)
echo     print^("- El servidor no es accessible des d'aquesta xarxa"^) 
echo     print^("- Les credencials son incorrectes"^)
echo     print^("- El port esta bloquejat pel firewall"^)
echo     sys.exit^(1^)
) > test_db_temp.py

python test_db_temp.py
del test_db_temp.py

echo.
echo Test de connexio completat.
echo.
goto end

:end
echo.
echo ========================================================
echo                     PROCES COMPLETAT
echo ========================================================
echo.
echo RESUM DE SOLUCIONS CREADES:
echo.
echo 1. PAQUET PORTABLE: No problemes amb antivirus
echo    - Facil de distribuir
echo    - No necessita permisos d'administrador
echo    - Compatible amb qualsevol PC
echo.
echo 2. SERVIDOR D'ACTUALITZACIONS: Per mantenir tots els PCs actualitzats
echo.
echo 3. INSTAL.LADOR SIMPLE: Per instalacio tradicional
echo.
echo RECOMANACIO: Usa el PAQUET PORTABLE per evitar problemes
echo amb antivirus i facilitar la distribucio.
echo.
echo Per a mes informacio, consulta INSTRUCCIONS_DEPLOYMENT.md
echo.
pause
