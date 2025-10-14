@echo off
echo ===============================================
echo    CREAR PAQUET DISTRIBUCIÓ PythonTecnica
echo ===============================================
echo.

echo Creant paquet complet per distribució...
echo.

set "dist_folder=PythonTecnica_DISTRIBUCIO"

echo 1. Creant carpeta de distribució...
if exist "%dist_folder%" rmdir /s /q "%dist_folder%"
mkdir "%dist_folder%"

echo 2. Copiant fitxers essencials...
copy "main_app.py" "%dist_folder%\"
copy "requirements.txt" "%dist_folder%\"
copy "SETUP.bat" "%dist_folder%\"
copy "RUN_APP.bat" "%dist_folder%\"
copy "VERIFY_SYSTEM.bat" "%dist_folder%\"
copy "CLEAN.bat" "%dist_folder%\"
copy "INSTRUCCIONS_RAPIDES.txt" "%dist_folder%\"
copy "GUIA_USUARIS_FINALS.md" "%dist_folder%\"

echo 3. Copiant carpetes necessàries...
xcopy /E /I "src" "%dist_folder%\src"
xcopy /E /I "config" "%dist_folder%\config"
xcopy /E /I "assets" "%dist_folder%\assets"
xcopy /E /I "i18n" "%dist_folder%\i18n"

echo 4. Creant carpetes de dades...
mkdir "%dist_folder%\data"
mkdir "%dist_folder%\data\raw"
mkdir "%dist_folder%\data\processed"
mkdir "%dist_folder%\data\reports"
mkdir "%dist_folder%\logs"
mkdir "%dist_folder%\sessions"

echo 5. Creant README per distribució...
echo # PythonTecnica SOME - Paquet d'Instal·lació > "%dist_folder%\README_DISTRIBUCIO.txt"
echo. >> "%dist_folder%\README_DISTRIBUCIO.txt"
echo INSTRUCCIONS RÀPIDES: >> "%dist_folder%\README_DISTRIBUCIO.txt"
echo 1. Llegir INSTRUCCIONS_RAPIDES.txt >> "%dist_folder%\README_DISTRIBUCIO.txt"
echo 2. Instal·lar Python amb "Add to PATH" >> "%dist_folder%\README_DISTRIBUCIO.txt"
echo 3. Executar SETUP.bat >> "%dist_folder%\README_DISTRIBUCIO.txt"
echo 4. Executar RUN_APP.bat >> "%dist_folder%\README_DISTRIBUCIO.txt"

echo 6. Eliminant fitxers innecessaris...
del /q "%dist_folder%\src\__pycache__\" 2>nul
for /r "%dist_folder%" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /r "%dist_folder%" %%f in (*.pyc) do @if exist "%%f" del /q "%%f" 2>nul

echo.
echo ===============================================
echo    PAQUET CREAT CORRECTAMENT!
echo ===============================================
echo.
echo El paquet està a la carpeta: %dist_folder%
echo.
echo Podeu:
echo 1. Comprimir aquesta carpeta en ZIP
echo 2. Distribuir-la als usuaris finals
echo 3. Els usuaris només han d'extreure i executar SETUP.bat
echo.

echo Contingut del paquet:
dir "%dist_folder%" /b

echo.
set /p compress="Voleu crear un ZIP automàticament? (S/N): "
if /i "%compress%"=="S" (
    echo Creant ZIP...
    powershell Compress-Archive -Path "%dist_folder%" -DestinationPath "PythonTecnica_DISTRIBUCIO.zip" -Force
    echo [OK] ZIP creat: PythonTecnica_DISTRIBUCIO.zip
)

echo.
pause