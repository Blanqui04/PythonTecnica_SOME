@echo off
echo ===============================================
echo    SETUP MILLORAT - PythonTecnica SOME
echo    AMB GESTIO D'ERRORS C++ BUILD TOOLS
echo ===============================================
echo.

REM Comprovar si Python està instal·lat
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no està instal·lat o no està al PATH
    echo Descarrega Python des de: https://www.python.org/downloads/
    echo Assegureu-vos de marcar "Add Python to PATH" durant la instal·lació
    pause
    exit /b 1
)

echo [OK] Python detectat:
python --version

echo.
echo Creant entorn virtual...
python -m venv venv

echo.
echo Activant entorn virtual...
call venv\Scripts\activate.bat

echo.
echo Actualitzant pip...
python -m pip install --upgrade pip

echo.
echo Intentant instal·lació de dependències...

REM Primer intent amb requirements normal
echo [INFO] Provant instal·lació amb totes les dependències...
pip install -r requirements.txt >nul 2>&1

if errorlevel 1 (
    echo.
    echo [WARNING] Error detectat durant la instal·lació!
    echo [INFO] Possible problema amb statsmodels i Visual C++
    echo.
    
    REM Verificar si existeix requirements_compatible.txt
    if exist "requirements_compatible.txt" (
        echo [INFO] Usant versió compatible sense statsmodels...
        pip install -r requirements_compatible.txt
        
        if errorlevel 1 (
            echo.
            echo [ERROR] Error persistent durant la instal·lació
            echo.
            echo POSSIBLES SOLUCIONS:
            echo 1. Instal·lar Microsoft C++ Build Tools:
            echo    Executar: instalacio\INSTALL_CPP_TOOLS.bat
            echo.
            echo 2. Executar aquest script com a administrador
            echo.
            echo 3. Comprovar connexió a internet
            echo.
            pause
            exit /b 1
        ) else (
            echo.
            echo [OK] Instal·lació completada amb versió compatible!
            echo [INFO] Algunes funcions estadístiques avançades podrien no estar disponibles
        )
    ) else (
        echo.
        echo [ERROR] No s'ha pogut instal·lar les dependències
        echo.
        echo INSTRUCCIONS PER SOLUCIONAR:
        echo.
        echo 1. INSTAL·LAR C++ BUILD TOOLS:
        echo    Executar: instalacio\INSTALL_CPP_TOOLS.bat
        echo.
        echo 2. TORNAR A EXECUTAR AQUEST SCRIPT
        echo.
        pause
        exit /b 1
    )
) else (
    echo [OK] Totes les dependències instal·lades correctament!
)

echo.
echo ===============================================
echo    CONFIGURACIO COMPLETADA!
echo ===============================================
echo.
echo Per executar l'aplicació, utilitzeu: RUN_APP.bat
echo.
echo SCRIPTS ADICIONALS DISPONIBLES:
echo - instalacio\VERIFY_CPP_TOOLS.bat (verificar Build Tools)
echo - instalacio\INSTALL_CPP_TOOLS.bat (guia Build Tools)
echo.
pause