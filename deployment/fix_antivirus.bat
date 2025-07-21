@echo off
title SOLUCIO PROBLEMES ANTIVIRUS - PythonTecnica_SOME
color 0C

echo.
echo ========================================================
echo         SOLUCIONADOR DE PROBLEMES ANTIVIRUS
echo              PythonTecnica_SOME
echo ========================================================
echo.
echo Has tingut problemes instalant PyInstaller o altres
echo dependencies per culpa de l'antivirus.
echo.
echo Aquest script ofereix solucions alternatives.
echo.
pause

echo.
echo PROBLEMA DETECTAT:
echo "OSError: [Errno 22] Invalid argument" amb PyInstaller
echo.
echo CAUSA:
echo L'antivirus bloqueja la instalacio o execucio de PyInstaller
echo perque pot semblar sospitos (crea executables).
echo.
echo SOLUCIONS DISPONIBLES:
echo.
echo 1. Crear paquet portable (RECOMANAT - sense compilar)
echo 2. Configurar exclusions a l'antivirus
echo 3. Instalacio manual step-by-step
echo 4. Usar versio pre-compilada
echo 5. Deployment de codi font directe
echo.

:menu
set /p choice="Escull una solucio (1-5): "

if "%choice%"=="1" goto portable_solution
if "%choice%"=="2" goto antivirus_config
if "%choice%"=="3" goto manual_install
if "%choice%"=="4" goto precompiled
if "%choice%"=="5" goto source_deploy

echo Opcio no valida. Si us plau, escull 1-5.
goto menu

:portable_solution
echo.
echo ========================================================
echo                SOLUCIO 1: PAQUET PORTABLE
echo ========================================================
echo.
echo Aquesta es la millor solucio! No necessites compilar res.
echo L'aplicacio s'executa directament amb Python.
echo.
echo AVANTATGES:
echo + No problemes amb antivirus
echo + No necessita PyInstaller
echo + Facil de distribuir
echo + Actualitzacions simples
echo.
echo Executant creacio de paquet portable...
echo.

REM Verificar que existeix deploy_portable.bat
if not exist "deploy_portable.bat" (
    echo ERROR: No es troba deploy_portable.bat
    echo Aquest fitxer hauria d'estar al mateix directori.
    pause
    goto end
)

REM Executar el script portable
call deploy_portable.bat
goto end

:antivirus_config
echo.
echo ========================================================
echo           SOLUCIO 2: CONFIGURAR ANTIVIRUS
echo ========================================================
echo.
echo Per fer funcionar PyInstaller, has d'afegir exclusions
echo a l'antivirus per a aquestes carpetes i processos:
echo.
echo CARPETES A EXCLOURE:
echo - %TEMP%
echo - %LOCALAPPDATA%\pip
echo - C:\Users\%USERNAME%\AppData\Local\Temp
echo - El directori del teu projecte
echo.
echo PROCESSOS A EXCLOURE:
echo - python.exe
echo - pip.exe  
echo - pyinstaller.exe
echo.
echo PASSOS:
echo 1. Obre la configuracio del teu antivirus
echo 2. Cerca "Exclusions" o "Excepcions"
echo 3. Afegeix les carpetes i processos de dalt
echo 4. Reinicia i prova altra vegada
echo.
echo ANTIVIRUS COMUNS:
echo.
echo WINDOWS DEFENDER:
echo - Obre "Seguretat de Windows"
echo - Proteccio contra virus i amenaces
echo - Configuracio de proteccio contra virus i amenaces
echo - Afegir o eliminar exclusions
echo.
echo BITDEFENDER:
echo - Obre Bitdefender
echo - Proteccio ^> Antivirus ^> Exclusions
echo.
echo KASPERSKY:
echo - Obre Kaspersky ^> Configuracio ^> Exclusions
echo.
echo Vols que obri la configuracio de Windows Defender? (s/n)
set /p open_defender="Resposta: "
if /i "%open_defender%"=="s" start ms-settings:windowsdefender
echo.
goto end

:manual_install
echo.
echo ========================================================
echo          SOLUCIO 3: INSTALACIO MANUAL
echo ========================================================
echo.
echo Instalarem les dependencies una per una per evitar
echo problemes amb l'antivirus.
echo.

echo Pas 1: Netejant cache de pip...
pip cache purge

echo.
echo Pas 2: Actualitzant pip...
python -m pip install --upgrade pip

echo.
echo Pas 3: Instalant dependencies basiques...
pip install --user --no-cache-dir --timeout 60 PyQt5
echo PyQt5 instalat.

pip install --user --no-cache-dir --timeout 60 psycopg2-binary  
echo psycopg2-binary instalat.

pip install --user --no-cache-dir --timeout 60 pandas
echo pandas instalat.

pip install --user --no-cache-dir --timeout 60 numpy
echo numpy instalat.

pip install --user --no-cache-dir --timeout 60 matplotlib
echo matplotlib instalat.

pip install --user --no-cache-dir --timeout 60 requests
echo requests instalat.

pip install --user --no-cache-dir --timeout 60 flask
echo flask instalat.

echo.
echo Dependencies basiques instalades!
echo.
echo Ara pots usar el paquet portable o provar altres opcions.
echo.
goto end

:precompiled
echo.
echo ========================================================
echo        SOLUCIO 4: VERSIO PRE-COMPILADA
echo ========================================================
echo.
echo Si algu altre de l'empresa ja ha compilat l'aplicacio
echo en un PC sense problemes d'antivirus, pots usar
echo aquesta versio pre-compilada.
echo.
echo PASSOS:
echo 1. Demana a algu amb un PC sense restriccions que executi:
echo    deploy.bat i esculli l'opcio de build
echo.
echo 2. Que et passi la carpeta 'distribution_package' resultant
echo.
echo 3. Distribueix aquesta carpeta compilada a tots els PCs
echo.
echo ALTERNATIVA:
echo Usar un servidor de la empresa per compilar i distribuir.
echo.
goto end

:source_deploy
echo.
echo ========================================================
echo       SOLUCIO 5: DEPLOYMENT DE CODI FONT DIRECTE
echo ========================================================
echo.
echo La solucio mes simple: distribuir el codi font tal com esta
echo sense compilar res.
echo.

echo Creant paquet de codi font...

if not exist "source_package" mkdir source_package

echo Copiant codi font...
robocopy "." "source_package\PythonTecnica_SOME" /s /e ^
    /xd ".git" "__pycache__" "build" "dist" "source_package" ^
    /xf "*.pyc" "*.pyo" "*.log"

REM Crear launcher simple
(
echo @echo off
echo title PythonTecnica_SOME
echo echo Iniciant PythonTecnica_SOME...
echo cd /d "%%~dp0PythonTecnica_SOME"
echo python main_app.py
echo pause
) > "source_package\Executar.bat"

REM Crear instalador de dependencies
(
echo @echo off
echo title Instalador Dependencies
echo echo Instalant dependencies necessaries...
echo cd /d "%%~dp0PythonTecnica_SOME" 
echo pip install -r requirements_minimal.txt
echo echo Dependencies instalades!
echo pause
) > "source_package\Instalar_Dependencies.bat"

REM Crear instructions
(
echo PYTHONTECNICA_SOME - CODI FONT
echo ==============================
echo.
echo INSTRUCCIONS:
echo 1. Executa "Instalar_Dependencies.bat" la primera vegada
echo 2. Executa "Executar.bat" per iniciar l'aplicacio
echo.
echo REQUISITS:
echo - Python 3.8+ instalat
echo - Connexio a la xarxa de l'empresa
echo.
echo Aquest paquet conte tot el codi font sense compilar.
echo Es la solucio mes compatible i sense problemes d'antivirus.
) > "source_package\LLEGEIX_PRIMER.txt"

echo.
echo PAQUET DE CODI FONT CREAT!
echo ==========================
echo.
echo Ubicacio: source_package\
echo.
echo Aquest paquet es pot distribuir sense problemes d'antivirus.
echo Els usuaris nomes necessiten Python instalat.
echo.
goto end

:end
echo.
echo ========================================================
echo                 SOLUCIONS COMPLETADES
echo ========================================================
echo.
echo Has vist totes les opcions disponibles per evitar
echo problemes amb l'antivirus.
echo.
echo RECOMANACIO:
echo La SOLUCIO 1 (Paquet Portable) es la millor opcio
echo per a la majoria de casos empresarials.
echo.
echo Si continues tenint problemes:
echo - Contacta amb l'equip IT per configurar exclusions
echo - Usa un PC diferent per crear el build
echo - Considera usar la distribucio de codi font directe
echo.
pause
