@echo off
REM ========================================
REM Crear Accés Directe a l'Escriptori
REM ========================================
echo.
echo Creant acces directe a l'escriptori...
echo.

REM Obtenir ruta actual
set CURRENT_DIR=%~dp0

REM Crear script VBS temporal per crear l'accés directe
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\PythonTecnica SOME.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%CURRENT_DIR%run_app.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%CURRENT_DIR%" >> CreateShortcut.vbs
echo oLink.Description = "PythonTecnica SOME - Aplicacio de Control de Qualitat" >> CreateShortcut.vbs
echo oLink.IconLocation = "%CURRENT_DIR%assets\images\gui\app_icon.ico" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

REM Executar el script VBS
cscript CreateShortcut.vbs //nologo

REM Eliminar script temporal
del CreateShortcut.vbs

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
