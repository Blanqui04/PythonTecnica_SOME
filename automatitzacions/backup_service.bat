@echo off
echo ==============================================
echo SERVEI DE BACKUP AUTOMATIC GOMPC
echo ==============================================
echo.
echo Iniciant servei de backup cada 24 hores...
echo Per aturar el servei: Ctrl+C
echo.

python backup_service.py

echo.
echo Servei finalitzat.
pause
