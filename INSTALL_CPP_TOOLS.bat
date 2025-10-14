@echo off
echo ===============================================
echo    INSTAL·LADOR C++ BUILD TOOLS
echo    PythonTecnica SOME
echo ===============================================
echo.

echo Aquest script us ajudara a instal·lar Microsoft C++ Build Tools
echo necessaris per a algunes llibreries Python com statsmodels.
echo.

set /p confirm="Voleu continuar amb la instal·lació? (S/N): "
if /i not "%confirm%"=="S" (
    echo Instal·lació cancel·lada
    pause
    exit /b 0
)

echo.
echo PASSOS A SEGUIR:
echo.
echo 1. DESCARREGAR BUILD TOOLS
echo ==========================
echo.
echo El navegador s'obrira per descarregar els Build Tools...
start "" "https://visualstudio.microsoft.com/visual-cpp-build-tools/"

echo.
echo Espereu que es descarregui vs_buildtools.exe
echo.
pause

echo.
echo 2. INSTRUCCIONS D'INSTAL·LACIÓ
echo ===============================
echo.
echo Quan executeu vs_buildtools.exe:
echo.
echo a) Executar com a ADMINISTRADOR (clic dret)
echo b) Seleccionar "C++ build tools"
echo c) A la dreta, marcar:
echo    - MSVC v143 - VS 2022 C++ x64/x86 build tools
echo    - Windows 11 SDK (ultima versió)
echo    - CMake tools for Visual Studio
echo d) Clic "Install"
echo e) Esperar 15-20 minuts
echo f) REINICIAR EL PC quan acabi
echo.

echo 3. VERIFICAR INSTAL·LACIÓ
echo ==========================
echo.
echo Després de reiniciar, executeu:
echo VERIFY_CPP_TOOLS.bat
echo.

echo 4. TORNAR A EXECUTAR SETUP
echo ===========================
echo.
echo Finalment, executeu altre cop:
echo SETUP.bat o SETUP_ENHANCED.bat
echo.

echo ===============================================
echo    NOTES IMPORTANTS:
echo ===============================================
echo.
echo - La instal·lació ocupa uns 3-4 GB
echo - Necessiteu connexió a internet
echo - Cal executar com a administrador
echo - OBLIGATORI reiniciar després
echo.
echo ALTERNATIVA: Si no voleu instal·lar Build Tools,
echo podeu usar SETUP_ENHANCED.bat que detecta l'error
echo i usa una versió compatible sense statsmodels.
echo.
pause