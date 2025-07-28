@echo off
echo ========================================
echo FIX DATABASE ENCODING AND PRECISION
echo ========================================
echo.
echo Aquest script soluciona problemes d'encoding Unicode
echo i millora la precisio decimal a la base de dades.
echo.
echo IMPORTANT: Assegura't que la base de dades esta accessible
echo.
pause

echo Executant correccio d'encoding...
python fix_database_encoding.py

echo.
echo ========================================
echo CORRECCIO COMPLETADA
echo ========================================
echo.
echo Ara pots fer servir les consultes del fitxer:
echo safe_database_queries.sql
echo.
echo Per exemple, a la teva base de dades executa:
echo SET CLIENT_ENCODING TO 'UTF8';
echo SELECT * FROM mesuresqualitat WHERE client LIKE 'BROSE%%';
echo.
pause
