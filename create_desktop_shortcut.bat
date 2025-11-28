@echo off
REM ========================================
REM Crear Accés Directe a l'Escriptori
REM ========================================
echo.
echo Creant acces directe a l'escriptori...
echo.

REM Obtenir ruta actual
set CURRENT_DIR=%~dp0

REM Eliminar barra final si existeix
if "%CURRENT_DIR:~-1%"=="\" set CURRENT_DIR=%CURRENT_DIR:~0,-1%

REM Crear script PowerShell temporal per crear l'accés directe
echo $WshShell = New-Object -comObject WScript.Shell; > CreateShortcut.ps1
echo $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\PythonTecnica SOME.lnk"); >> CreateShortcut.ps1
echo $Shortcut.TargetPath = "%CURRENT_DIR%\run_app.bat"; >> CreateShortcut.ps1
echo $Shortcut.WorkingDirectory = "%CURRENT_DIR%"; >> CreateShortcut.ps1
echo $Shortcut.Description = "PythonTecnica SOME - Aplicacio de Control de Qualitat"; >> CreateShortcut.ps1
echo $Shortcut.IconLocation = "%CURRENT_DIR%\assets\images\gui\app_icon.ico"; >> CreateShortcut.ps1
echo $Shortcut.Save(); >> CreateShortcut.ps1

REM Executar el script PowerShell
powershell -ExecutionPolicy Bypass -File CreateShortcut.ps1

REM Eliminar script temporal
del CreateShortcut.ps1

echo.
echo ========================================
echo [OK] Acces directe creat a l'escriptori!
echo ========================================
echo.
echo Nom: "PythonTecnica SOME"
echo.
echo Ara pots executar l'aplicacio fent doble clic a l'icona.
echo.
pause
