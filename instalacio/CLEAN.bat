@echo off
echo ===============================================
echo    NETEJA ENTORN PYTHONTECNICA
echo ===============================================
echo.

echo ATENCIO: Això eliminarà l'entorn virtual actual
echo Haureu de tornar a executar SETUP.bat després
echo.
set /p confirm="Esteu segur? (S/N): "

if /i "%confirm%"=="S" (
    echo.
    echo Eliminant entorn virtual...
    if exist "venv" (
        rmdir /s /q venv
        echo [OK] Entorn virtual eliminat
    ) else (
        echo [INFO] No hi havia entorn virtual
    )
    
    echo.
    echo Netejant fitxers cache...
    for /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
    echo [OK] Cache Python netejat
    
    echo.
    echo ===============================================
    echo    NETEJA COMPLETADA
    echo ===============================================
    echo Executeu SETUP.bat per tornar a configurar
) else (
    echo Operació cancel·lada
)

echo.
pause