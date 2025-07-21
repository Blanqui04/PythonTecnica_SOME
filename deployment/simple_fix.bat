@echo off
title SOLUCIO SIMPLE - SIN ANTIVIRUS PROBLEMS
color 0A

echo.
echo =========================================
echo    SOLUCIO SIMPLE ANTI-ANTIVIRUS  
echo      PythonTecnica_SOME v1.0
echo =========================================
echo.
echo Aquesta solucio evita TOTS els problemes
echo amb antivirus creant un paquet portable.
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no trobat. Instal.la Python primer.
    pause
    exit /b 1
)

echo Python OK!
echo.
echo Creant paquet portable...

REM Crear directori
if not exist "PAQUET_FINAL" mkdir PAQUET_FINAL

REM Copiar tot
echo Copiant aplicacio...
robocopy "." "PAQUET_FINAL" /s /e /xd ".git" "__pycache__" "PAQUET_FINAL" /xf "*.pyc"

REM Crear launcher
echo Creant launcher...
(
echo @echo off
echo title PythonTecnica_SOME
echo cd /d "%%~dp0"
echo echo Iniciant PythonTecnica_SOME...
echo echo Conectant a BBDD: 172.26.5.159:5433
echo python main_app.py
echo pause
) > "PAQUET_FINAL\EXECUTAR.bat"

REM Crear instalador dependencies
(
echo @echo off
echo echo Instalant dependencies...
echo pip install PyQt5 psycopg2-binary pandas numpy matplotlib requests
echo echo Fet! Ara executa EXECUTAR.bat
echo pause
) > "PAQUET_FINAL\INSTALAR_DEPENDENCIES.bat"

REM Instructions
(
echo INSTRUCCIONS SIMPLES:
echo 1. Executa INSTALAR_DEPENDENCIES.bat ^(primera vegada^)
echo 2. Executa EXECUTAR.bat
echo.
echo Ja esta! Sense compilacions ni antivirus problems.
) > "PAQUET_FINAL\INSTRUCCIONS.txt"

echo.
echo COMPLETAT!
echo ==========
echo.
echo Paquet creat a: PAQUET_FINAL\
echo.
echo Per distribuir:
echo 1. Copia la carpeta PAQUET_FINAL a cada PC
echo 2. Executa INSTALAR_DEPENDENCIES.bat la primera vegada
echo 3. Usa EXECUTAR.bat per iniciar sempre
echo.
echo Cap problema amb antivirus garantit!
echo.
pause
