@echo off
echo ===============================================
echo    VERIFICADOR C++ BUILD TOOLS
echo ===============================================
echo.

echo Verificant si Microsoft C++ Build Tools estan instal·lats...
echo.

REM Verificar Visual Studio Build Tools
set "vs_path_found=0"

REM Buscar en ubicacions comunes de Visual Studio
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC" (
    echo [OK] Visual Studio 2022 Build Tools detectats
    set "vs_path_found=1"
)

if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    echo [OK] Visual Studio 2022 Community detectat
    set "vs_path_found=1"
)

if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Tools\MSVC" (
    echo [OK] Visual Studio 2019 Build Tools detectats
    set "vs_path_found=1"
)

if "%vs_path_found%"=="0" (
    echo [ERROR] Microsoft C++ Build Tools NO detectats
    echo.
    echo NECESSITEU INSTAL·LAR:
    echo 1. Executar INSTALL_CPP_TOOLS.bat
    echo 2. O anar manualment a:
    echo    https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo.
) else (
    echo.
    echo [OK] C++ Build Tools semblen estar instal·lats correctament!
)

echo.
echo Verificant compilador cl.exe...

REM Intentar trobar cl.exe
where cl >nul 2>&1
if errorlevel 1 (
    echo [WARNING] cl.exe no està al PATH
    echo Això és normal, es configura automàticament durant la compilació
) else (
    echo [OK] cl.exe detectat al PATH
)

echo.
echo Testejant instal·lació amb un paquet simple que requereix compilació...

REM Crear entorn temporal per test
python -m venv test_venv >nul 2>&1
call test_venv\Scripts\activate.bat >nul 2>&1

echo Provant instal·lació de numpy (requereix compilació)...
pip install numpy>1.0 --no-cache-dir >nul 2>&1

if errorlevel 1 (
    echo [ERROR] Test de compilació fallit
    echo Els C++ Build Tools no funcionen correctament
) else (
    echo [OK] Test de compilació exitós!
    echo Els C++ Build Tools funcionen correctament
)

REM Netejar entorn temporal
call deactivate >nul 2>&1
if exist "test_venv" rmdir /s /q test_venv >nul 2>&1

echo.
echo ===============================================
echo    RESULTATS DE LA VERIFICACIÓ:
echo ===============================================

if "%vs_path_found%"=="1" (
    echo ✅ C++ Build Tools: INSTAL·LATS
) else (
    echo ❌ C++ Build Tools: NO INSTAL·LATS
)

echo.
echo Si tot està OK, podeu executar:
echo - SETUP.bat (versió completa amb statsmodels)
echo - SETUP_ENHANCED.bat (detecta problemes automàticament)
echo.
pause