@echo off
setlocal EnableDelayedExpansion

echo ================================================
echo    INSTALADOR PythonTecnica_SOME v2.0
echo ================================================
echo.

REM Verificar si s'està executant com a administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Aquest script necessita permisos d'administrador.
    echo Si us plau, executa com a "Administrador"
    echo.
    pause
    exit /b 1
)

echo Comprovant sistema...
echo.

REM Comprovar si Python està instal·lat
set PYTHON_INSTALLED=0
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Python ja està instal·lat:
    python --version
    set PYTHON_INSTALLED=1
) else (
    echo Python no detectat. Procedint amb la instal·lació automàtica...
)

REM Si Python no està instal·lat, descarregar i instal·lar Python 3.11.9
if !PYTHON_INSTALLED! equ 0 (
    echo.
    echo ================================================
    echo    INSTAL·LANT PYTHON 3.11.9 (Versió Recomanada)
    echo ================================================
    echo.
    
    set PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    set PYTHON_INSTALLER=python-3.11.9-amd64.exe
    
    echo Descarregant Python 3.11.9...
    powershell -Command "& {Invoke-WebRequest -Uri '!PYTHON_URL!' -OutFile '!PYTHON_INSTALLER!'}"
    
    if not exist "!PYTHON_INSTALLER!" (
        echo ERROR: No s'ha pogut descarregar Python.
        echo Si us plau, descarrega manualment des de: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    echo Instal·lant Python 3.11.9...
    echo (Això pot trigar uns minuts...)
    "!PYTHON_INSTALLER!" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    if %errorlevel% neq 0 (
        echo ERROR: La instal·lació de Python ha fallat.
        pause
        exit /b 1
    )
    
    echo Netejant fitxers temporals...
    del "!PYTHON_INSTALLER!"
    
    echo Python 3.11.9 instal·lat correctament!
    echo.
    
    REM Actualitzar PATH per a aquesta sessió
    set PATH=%PATH%;C:\Program Files\Python311;C:\Program Files\Python311\Scripts
    
    REM Verificar la instal·lació
    timeout /t 3 /nobreak >nul
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo AVÍS: Python s'ha instal·lat però pot necessitar reiniciar.
        echo Si l'error persisteix, reinicia el PC i torna a executar aquest script.
        pause
        exit /b 1
    )
    
    echo Python verificat correctament!
)

echo.
echo ================================================
echo    INSTAL·LANT PythonTecnica_SOME
echo ================================================
echo.

REM Actualitzar pip a la última versió
echo Actualitzant pip...
python -m pip install --upgrade pip

REM Verificar si estem en el directori correcte
if not exist "requirements.txt" (
    if not exist "deployment\requirements.txt" (
        if not exist "..\config\requirements.txt" (
            echo ERROR: No es troba el fitxer requirements.txt
            echo Assegura't que estàs en el directori correcte del deployment.
            pause
            exit /b 1
        ) else (
            set REQ_PATH=..\config\requirements.txt
        )
    ) else (
        set REQ_PATH=deployment\requirements.txt
    )
) else (
    set REQ_PATH=requirements.txt
)

echo Instal·lant dependències Python...
pip install -r "!REQ_PATH!"

if %errorlevel% neq 0 (
    echo ERROR: No s'han pogut instal·lar les dependències.
    echo Verificant connectivitat a internet...
    ping google.com -n 1 >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERROR: No hi ha connexió a internet. Si us plau, connecta't i torna a intentar-ho.
    )
    pause
    exit /b 1
)

REM Executar instal·lador empresarial si existeix
if exist "deployment\enterprise_installer.py" (
    echo Configurant instal·lació empresarial...
    python deployment\enterprise_installer.py app
) else if exist "enterprise_installer.py" (
    echo Configurant instal·lació empresarial...
    python enterprise_installer.py app
) else (
    echo AVÍS: No es troba l'enterprise_installer.py
    echo L'aplicació s'ha configurat amb dependències bàsiques.
)

REM Verificar la instal·lació
echo.
echo Verificant la instal·lació...
if exist "app\PythonTecnica_SOME.exe" (
    echo ✓ Executable trobat: app\PythonTecnica_SOME.exe
) else if exist "..\dist\PythonTecnica_SOME\PythonTecnica_SOME.exe" (
    echo ✓ Executable trobat: ..\dist\PythonTecnica_SOME\PythonTecnica_SOME.exe
) else (
    echo AVÍS: No es troba l'executable. Pot ser que necessitis executar el build primer.
)

echo.
echo ================================================
echo    INSTAL·LACIÓ COMPLETADA!
echo ================================================
echo.
echo Python 3.11.9: Instal·lat ✓
echo Dependències: Instal·lades ✓
echo PythonTecnica_SOME: Configurat ✓
echo.
echo Pots executar l'aplicació des del menú d'inici o escriptori.
echo Si hi ha problemes, consulta els logs a: logs\app.log
echo.
echo Prem qualsevol tecla per finalitzar...
pause >nul
