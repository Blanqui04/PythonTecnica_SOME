@echo off
REM Script per copiar dades entre bases de dades
REM Copia mesuresqualitat de airflow_db a documentacio_tecnica

echo ===============================================
echo CÒPIA DE DADES ENTRE BASES DE DADES
echo ===============================================
echo.
echo Origen: airflow_db (config_2)
echo Destí: documentacio_tecnica (config_1) 
echo Taula: mesuresqualitat
echo.
echo ===============================================

REM Canviar al directori del projecte
cd /d "C:\Github\PythonTecnica_SOME\PythonTecnica_SOME"

REM Crear directori de logs si no existeix
if not exist "logs" mkdir logs

REM Executar script Python
echo Executant còpia de dades...
python scripts\copy_database_data.py

REM Pausar per veure els resultats
echo.
echo ===============================================
pause
